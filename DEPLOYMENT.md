# Deploying this existing publication with GitHub Actions

The reviewed production workflow is `.github/workflows/vercel-production.yml`.
It uses the official Vercel CLI, not the Vercel GitHub identity integration.
It targets only this existing benchmark project and preserves the existing URL:
https://aithos-vulkan-tensor-parallel.vercel.app . It does not change the separate corporate website.

The `benchmark-production` Environment must permit deployments only from branch `main`, with no tag policy. Store these three values in this repository's **Settings → Environments → benchmark-production → Environment secrets**:

- `VERCEL_TOKEN`: a dedicated Vercel access token with access to the existing Aithos Innovation team/project. Create through Vercel's normal Tokens settings. Scope it only to the existing Aithos Innovation team, choose the shortest practical lifetime and rotate before expiry. Team tokens may reach other projects in that team; the workflow destination guards prevent accidental deployment elsewhere but do not narrow the token itself. Only trusted main maintainers should be able to modify this workflow. Do not export an interactive CLI access/refresh credential or paste a token in an issue, commit, workflow input or chat.
- `VERCEL_ORG_ID`: the existing team's `orgId`.
- `VERCEL_PROJECT_ID`: the existing benchmark `projectId`.

The project/team IDs come from the existing project, not a newly created one. The workflow compares their digests against the approved destination before any deployment. Do not substitute the corporate website's project ID.

Only pushes to `main`, or manual runs on `main`, can deploy. There is no pull-request/fork deployment. The GitHub token has read-only contents permission; checkout does not persist it. The Vercel token is step-scoped and is not exposed to dependency installation. Only this main-restricted Environment releases the token; untrusted branches and forks cannot access it. Main writers are trusted production maintainers; main branch policy is unchanged. Action revisions and the tested Vercel CLI/Node versions are pinned. Measurement/file validation precedes deployment; missing credentials or wrong destination IDs stop the job. Concurrency serializes production deployment jobs. A current-main SHA guard rejects stale manual reruns. The CLI reads its token only from the step environment, not command-line arguments.

This is a static project with no build command and no project environment variables. A direct `vercel deploy --prod` is sufficient: no environment pull, custom build pipeline, additional service, new project or domain change is needed. Production deployment is followed by byte-for-byte checks of eight live resources and the four canonical documentation links, first at the immutable deployment URL and then at the existing production alias; the verifier allows three bounded attempts for propagation. A post-deploy check detects problems but does not automatically roll back; preserve existing deployment history and inspect/revert through the existing project if necessary.

To validate initial automation after configuring secrets, push one reviewed documentation-only change to `main`. Check the Actions run, the new deployment in the SAME project, its commit SHA, the unchanged production alias and `scripts/verify_site.py`. A manual CLI deployment is not evidence of GitHub Actions automation. Manual `workflow_dispatch` is available to retry after correcting an authorization problem.

No secrets or deployment output files are uploaded as Actions artifacts. Do not enable shell tracing or print environment variables. Workflow edits are production-sensitive and should receive an independent review.

Official reference: https://vercel.com/kb/guide/how-can-i-use-github-actions-with-vercel
