[01:13:47.440] Running build in Washington, D.C., USA (East) – iad1
[01:13:47.441] Build machine configuration: 2 cores, 8 GB
[01:13:47.480] Cloning github.com/tadams95/4ex.ninja (Branch: main, Commit: e074b66)
[01:13:48.553] Cloning completed: 1.073s
[01:13:54.177] Restored build cache from previous deployment (SxV7B3nuJHz5wD4rZqMtLqf7Xq98)
[01:14:06.205] Running "vercel build"
[01:14:06.671] Vercel CLI 44.7.3
[01:14:06.998] Installing dependencies...
[01:14:09.710] npm warn ERESOLVE overriding peer dependency
[01:14:09.711] npm warn While resolving: use-sync-external-store@1.2.0
[01:14:09.711] npm warn Found: react@19.1.1
[01:14:09.711] npm warn node_modules/react
[01:14:09.711] npm warn   react@"^19.0.0" from the root project
[01:14:09.711] npm warn   18 more (zustand, @coinbase/onchainkit, zustand, ...)
[01:14:09.712] npm warn
[01:14:09.712] npm warn Could not resolve dependency:
[01:14:09.712] npm warn peer react@"^16.8.0 || ^17.0.0 || ^18.0.0" from use-sync-external-store@1.2.0
[01:14:09.712] npm warn node_modules/valtio/node_modules/use-sync-external-store
[01:14:09.712] npm warn   use-sync-external-store@"1.2.0" from valtio@1.13.2
[01:14:09.712] npm warn   node_modules/valtio
[01:14:09.712] npm warn
[01:14:09.712] npm warn Conflicting peer dependency: react@18.3.1
[01:14:09.712] npm warn node_modules/react
[01:14:09.713] npm warn   peer react@"^16.8.0 || ^17.0.0 || ^18.0.0" from use-sync-external-store@1.2.0
[01:14:09.713] npm warn   node_modules/valtio/node_modules/use-sync-external-store
[01:14:09.713] npm warn     use-sync-external-store@"1.2.0" from valtio@1.13.2
[01:14:09.713] npm warn     node_modules/valtio
[01:14:10.406] 
[01:14:10.407] up to date in 3s
[01:14:10.408] 
[01:14:10.408] 273 packages are looking for funding
[01:14:10.408]   run `npm fund` for details
[01:14:10.437] Detected Next.js version: 15.4.6
[01:14:10.437] Running "npm run vercel-build"
[01:14:10.544] 
[01:14:10.544] > 4ex.ninja-frontend@0.1.0 vercel-build
[01:14:10.544] > next build
[01:14:10.545] 
[01:14:11.279]    ▲ Next.js 15.4.6
[01:14:11.280]    - Experiments (use with caution):
[01:14:11.280]      · optimizePackageImports
[01:14:11.280] 
[01:14:11.348]    Creating an optimized production build ...
[01:14:31.580] Failed to compile.
[01:14:31.580] 
[01:14:31.581] ./src/utils/checkout-helpers.js
[01:14:31.581] Module not found: Can't resolve './get-stripe'
[01:14:31.581] 
[01:14:31.581] https://nextjs.org/docs/messages/module-not-found
[01:14:31.581] 
[01:14:31.582] Import trace for requested module:
[01:14:31.582] ./src/app/account/page.js
[01:14:31.582] 
[01:14:31.582] ./src/app/api/update-profile/route.js
[01:14:31.582] Module not found: Can't resolve '../auth/[...nextauth]/auth-options'
[01:14:31.583] 
[01:14:31.583] https://nextjs.org/docs/messages/module-not-found
[01:14:31.583] 
[01:14:31.583] ./src/app/api/user-profile/route.js
[01:14:31.583] Module not found: Can't resolve '../auth/[...nextauth]/auth-options'
[01:14:31.584] 
[01:14:31.584] https://nextjs.org/docs/messages/module-not-found
[01:14:31.584] 
[01:14:31.596] 
[01:14:31.596] > Build failed because of webpack errors
[01:14:31.671] Error: Command "npm run vercel-build" exited with 1