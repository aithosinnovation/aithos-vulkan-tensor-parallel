// Private experiment harness. The pinned llama.cpp source is unchanged.
#define NOMINMAX
#include <windows.h>
#include "llama.h"
#include "ggml-backend.h"
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Clock = std::chrono::steady_clock;
static const auto started = Clock::now();
static double seconds() { return std::chrono::duration<double>(Clock::now()-started).count(); }
static std::string json_quote(const std::string & s) {
    std::ostringstream out; out << '"';
    for (unsigned char c : s) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << int(c) << std::dec;
        else out << c;
    }
    out << '"'; return out.str();
}
static void event(const char * name, const std::string & extra = "") {
    std::cout << "{\"event\":" << json_quote(name) << ",\"elapsed_seconds\":" << std::fixed << std::setprecision(9) << seconds() << extra << "}\n" << std::flush;
}
static std::string hex(const std::string & data) {
    std::ostringstream out;
    for (unsigned char b : data) out << std::hex << std::setw(2) << std::setfill('0') << int(b);
    return out.str();
}
static bool repeated(const std::vector<llama_token> & tokens) {
    // Stop on eight identical tokens or three copies of a four-token block.
    size_t n = tokens.size();
    if (n >= 8) {
        bool same = true; for (size_t j = n-7; j < n; ++j) same = same && tokens[j] == tokens[n-8];
        if (same) return true;
    }
    if (n >= 12) {
        bool same = true; for (size_t j = 0; j < 8; ++j) same = same && tokens[n-12+j] == tokens[n-8+j];
        if (same) return true;
    }
    return false;
}
int main(int argc, char ** argv) {
    try {
        if (argc != 6) throw std::runtime_error("usage: correctness MODEL DEVICE_CSV none|tensor OUTPUT_DIRECTORY REFERENCE_TOKENS");
        std::ifstream teacher_file(argv[5]);
        std::vector<llama_token> teacher; int token;
        while (teacher_file >> token) teacher.push_back(token);
        if (!teacher_file.eof() || teacher.size() != 32) throw std::runtime_error("expected exactly 32 teacher IDs");
        const std::string mode = argv[3];
        if (mode != "layer") throw std::runtime_error("invalid split mode");
        const std::string prefix = std::string(argv[4]) + "\\";
        for (const char * file : {"logits.f32", "generated.bin"}) {
            if (GetFileAttributesA((prefix + file).c_str()) != INVALID_FILE_ATTRIBUTES) throw std::runtime_error("output already exists; refusing retry");
        }
        char executable[MAX_PATH];
        DWORD count = GetModuleFileNameA(nullptr, executable, MAX_PATH);
        if (!count || count >= MAX_PATH) throw std::runtime_error("executable path unavailable");
        std::string bin(executable, count); bin = bin.substr(0, bin.find_last_of("\\/"));
        ggml_backend_load_all_from_path(bin.c_str());
        llama_backend_init();
        std::vector<ggml_backend_dev_t> devices;
        std::stringstream input(argv[2]); std::string name;
        while (std::getline(input, name, ',')) {
            auto dev = ggml_backend_dev_by_name(name.c_str());
            if (!dev) throw std::runtime_error("requested device missing: " + name);
            devices.push_back(dev);
            event("selected_device", ",\"name\":" + json_quote(name) + ",\"description\":" + json_quote(ggml_backend_dev_description(dev)));
        }
        if (devices.size() != (mode == "none" ? 1u : 2u)) throw std::runtime_error("incorrect selected-device count");
        const std::string first = ggml_backend_dev_description(devices[0]);
        if (first.find("RTX 3090") == std::string::npos && first.find("B70") == std::string::npos) throw std::runtime_error("control is not B70 or RTX3090");
        if (mode == "layer" && (first.find("B70") == std::string::npos || std::string(ggml_backend_dev_description(devices[1])).find("RTX 3090") == std::string::npos)) throw std::runtime_error("mixed devices are not B70 then RTX3090");
        devices.push_back(nullptr);
        char loader[MAX_PATH] = {};
        auto module = GetModuleHandleA("vulkan-1.dll");
        if (!module || !GetModuleFileNameA(module, loader, MAX_PATH)) throw std::runtime_error("loaded Vulkan loader path unavailable");
        event("loader", ",\"path\":" + json_quote(loader));
        std::vector<float> split(llama_max_devices(), 0.0f); split[0] = split[1] = 1.0f;
        auto mp = llama_model_default_params();
        mp.devices = devices.data(); mp.n_gpu_layers = 99; mp.main_gpu = 0;
        mp.split_mode = mode == "none" ? LLAMA_SPLIT_MODE_NONE : LLAMA_SPLIT_MODE_LAYER;
        mp.tensor_split = mode == "layer" ? split.data() : nullptr;
        mp.load_mode = LLAMA_LOAD_MODE_MMAP; mp.lazy_mode = LLAMA_LAZY_MODE_OFF;
        event("model_load_begin");
        std::unique_ptr<llama_model, decltype(&llama_model_free)> model(llama_model_load_from_file(argv[1], mp), llama_model_free);
        if (!model) throw std::runtime_error("model initialization failed");
        event("model_load_end");
        auto cp = llama_context_default_params();
        cp.n_ctx = 512; cp.n_batch = cp.n_ubatch = 32; cp.n_seq_max = 1;
        cp.n_threads = cp.n_threads_batch = 4; cp.flash_attn_type = LLAMA_FLASH_ATTN_TYPE_ENABLED;
        cp.type_k = cp.type_v = GGML_TYPE_F16; cp.no_perf = false;
        cp.samplers = nullptr; cp.n_samplers = 0;
        event("context_begin");
        std::unique_ptr<llama_context, decltype(&llama_free)> ctx(llama_init_from_model(model.get(), cp), llama_free);
        if (!ctx) throw std::runtime_error("context initialization failed");
        event("context_ready");
        const auto vocab = llama_model_get_vocab(model.get());
        const int n_vocab = llama_vocab_n_tokens(vocab);
        if (n_vocab <= 0) throw std::runtime_error("invalid vocabulary size");
        for (auto t : teacher) if (t < 0 || t >= n_vocab || llama_vocab_is_eog(vocab,t)) throw std::runtime_error("invalid teacher token");
        const std::string prompt = "The capital of France is";
        std::vector<llama_token> prompt_tokens(32);
        int n = llama_tokenize(vocab, prompt.c_str(), static_cast<int32_t>(prompt.size()), prompt_tokens.data(), 32, true, false);
        if (n <= 0 || n > 32) throw std::runtime_error("prompt does not fit bounded batch");
        prompt_tokens.resize(n);
        std::string token_list;
        for (int i = 0; i < n; ++i) token_list += (i ? "," : "") + std::to_string(prompt_tokens[i]);
        event("capture_mode", ",\"mode\":\"teacher_forced\",\"predicted_output_semantics\":\"argmax at saved reference prefixes; not autonomous generation\"");
        event("prompt", ",\"text\":" + json_quote(prompt) + ",\"tokens\":[" + token_list + "],\"n_vocab\":" + std::to_string(n_vocab));
        std::ofstream logits_file(prefix + "logits.f32", std::ios::binary);
        std::ofstream text_file(prefix + "generated.bin", std::ios::binary);
        if (!logits_file || !text_file) throw std::runtime_error("cannot open output files");
        std::vector<llama_token> generated;
        std::string stop_reason = "token_limit";
        event("prompt_decode_begin");
        int status = llama_decode(ctx.get(), llama_batch_get_one(prompt_tokens.data(), n));
        if (status) throw std::runtime_error("prompt decode failed: " + std::to_string(status));
        event("prompt_decode_end");
        for (int step = 0; step < 32; ++step) {
            llama_synchronize(ctx.get());
            const float * logits = llama_get_logits_ith(ctx.get(), -1);
            if (!logits) throw std::runtime_error("no logits");
            logits_file.write(reinterpret_cast<const char *>(logits), static_cast<std::streamsize>(n_vocab)*sizeof(float));
            logits_file.flush();
            if (!logits_file) throw std::runtime_error("logit write failed");
            llama_token best = 0;
            for (int j = 0; j < n_vocab; ++j) {
                if (!std::isfinite(logits[j])) throw std::runtime_error("nonfinite logit at index " + std::to_string(j) + " value " + std::to_string(logits[j]));
                if (logits[j] > logits[best]) best = j;
            }
            const bool eog = llama_vocab_is_eog(vocab, best);
            std::vector<char> piece(256);
            int len = llama_token_to_piece(vocab, best, piece.data(), static_cast<int32_t>(piece.size()), 0, false);
            if (len < 0) {
                piece.resize(-len); len = llama_token_to_piece(vocab, best, piece.data(), static_cast<int32_t>(piece.size()), 0, false);
            }
            if (len < 0) throw std::runtime_error("invalid token piece");
            std::string bytes(piece.data(), len);
            event("token", ",\"step\":" + std::to_string(step) + ",\"id\":" + std::to_string(best) + ",\"logit\":" + std::to_string(logits[best]) + ",\"piece_hex\":" + json_quote(hex(bytes)) + ",\"eog\":" + (eog ? "true" : "false"));
            event("teacher", ",\"step\":" + std::to_string(step) + ",\"id\":" + std::to_string(teacher[step]));
            if (best != teacher[step]) throw std::runtime_error("top-token divergence against saved reference at step " + std::to_string(step));
            text_file.write(bytes.data(), len); text_file.flush();
            generated.push_back(best);
            if (!logits_file || !text_file) throw std::runtime_error("output write failed");
            // Predictions are not fed back; repetition is analyzed offline, not a context guard.
            if (step == 31) break;
            status = llama_decode(ctx.get(), llama_batch_get_one(&teacher[step], 1));
            if (status) throw std::runtime_error("generation decode failed: " + std::to_string(status));
        }
        const auto perf = llama_perf_context(ctx.get());
        event("engine_performance", ",\"prompt_tokens\":" + std::to_string(perf.n_p_eval) + ",\"generation_eval_steps\":" + std::to_string(perf.n_eval) + ",\"prompt_eval_ms\":" + std::to_string(perf.t_p_eval_ms) + ",\"generation_eval_ms\":" + std::to_string(perf.t_eval_ms));
        llama_perf_context_print(ctx.get());
        event("completed", ",\"generated_tokens\":" + std::to_string(generated.size()) + ",\"stop_reason\":" + json_quote(stop_reason));
        return 0;
    } catch (const std::exception & e) {
        event("failed", ",\"reason\":" + json_quote(e.what()));
        std::cerr << "Aithos correctness capture failed: " << e.what() << '\n';
        return 2;
    }
}
