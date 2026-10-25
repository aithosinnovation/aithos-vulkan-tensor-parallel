#include <windows.h>
#include <dxgi1_2.h>
#include <iostream>
#include <iomanip>
int main(){IDXGIFactory1*f=nullptr;if(FAILED(CreateDXGIFactory1(__uuidof(IDXGIFactory1),(void**)&f)))return 2;std::cout<<"[";bool first=true;for(UINT i=0;;++i){IDXGIAdapter1*a=nullptr;if(f->EnumAdapters1(i,&a)==DXGI_ERROR_NOT_FOUND)break;DXGI_ADAPTER_DESC1 d{};a->GetDesc1(&d);char s[256];WideCharToMultiByte(CP_UTF8,0,d.Description,-1,s,256,nullptr,nullptr);if(!first)std::cout<<",";first=false;std::cout<<"{\"name\":\""<<s<<"\",\"luid\":\"luid_0x"<<std::hex<<std::setw(8)<<std::setfill('0')<<(UINT)d.AdapterLuid.HighPart<<"_0x"<<std::setw(8)<<d.AdapterLuid.LowPart<<"\",\"dedicated_bytes\":"<<std::dec<<d.DedicatedVideoMemory<<",\"vendor_id\":"<<d.VendorId<<",\"device_id\":"<<d.DeviceId<<"}";a->Release();}std::cout<<"]\n";f->Release();}
