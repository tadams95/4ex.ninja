Error with Permissions-Policy header: Invalid allowlist item(*.coinbase.com) for feature clipboard-write. Allowlist item must be *, self or quoted url.Understand this warning
swap:1 Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Inter&display=swap' because it violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline' *.stripe.com *.coinbase.com". Note that 'style-src-elem' was not explicitly set, so 'style-src' is used as a fallback.
Understand this error
swap:1 Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Inter:wght@700&display=swap' because it violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline' *.stripe.com *.coinbase.com". Note that 'style-src-elem' was not explicitly set, so 'style-src' is used as a fallback.
Understand this error
swap:1 Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Oxanium:wght@200..800&display=swap' because it violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline' *.stripe.com *.coinbase.com". Note that 'style-src-elem' was not explicitly set, so 'style-src' is used as a fallback.
Understand this error
swap:1 Refused to load the stylesheet 'https://fonts.googleapis.com/css2?family=Noto+Sans+Mono:wght@100..900&display=swap' because it violates the following Content Security Policy directive: "style-src 'self' 'unsafe-inline' *.stripe.com *.coinbase.com". Note that 'style-src-elem' was not explicitly set, so 'style-src' is used as a fallback.
Understand this error
swap:1  GET http://localhost:3000/_next/static/chunks/main.js net::ERR_ABORTED 404 (Not Found)Understand this error
swap:1  GET http://localhost:3000/_next/static/chunks/framework.js net::ERR_ABORTED 404 (Not Found)

FetchUtil.ts:20 Refused to connect to 'https://api.web3modal.org/appkit/v1/config?projectId=54848d4e8a3a1da71c0400f011bfc230&st=appkit&sv=html-core-1.7.8' because it violates the following Content Security Policy directive: "connect-src 'self' *.stripe.com *.coinbase.com *.walletconnect.com *.walletconnect.org wss: ws: https://api.4ex.ninja wss://api.4ex.ninja wss://relay.walletconnect.com wss://relay.walletconnect.org https://mainnet.base.org https://sepolia.base.org https://base.llamarpc.com https://1rpc.io https://base.blockpi.network https://base-mainnet.public.blastapi.io https://base.drpc.org https://gateway.tenderly.co https://eth.merkle.io https://api.ensideas.com https://cloudflare-eth.com".

fetchData @ FetchUtil.ts:20
get @ FetchUtil.ts:44
fetchProjectConfig @ ApiController.ts:158
fetchRemoteFeatures @ ConfigUtil.ts:233
initialize @ appkit-base-client.ts:165
await in initialize
AppKitBaseClient @ appkit-base-client.ts:142
AppKit @ appkit-core.ts:34
createAppKit @ core.ts:12
initialize @ browser.js:8
await in initialize
init @ browser.js:8
initProvider @ walletConnect.ts:251
await in initProvider
getProvider @ walletConnect.ts:270
setup @ walletConnect.ts:118
setup @ createConfig.ts:107
(anonymous) @ createConfig.ts:71
createStoreImpl @ vanilla.mjs:19
createStore @ vanilla.mjs:22
createConfig @ createConfig.ts:67
[project]/src/lib/wagmi.ts [app-client] (ecmascript) @ wagmi.ts:5
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateModuleFromParent @ dev-base.ts:126
esmImport @ runtime-utils.ts:264
[project]/src/app/components/Providers.tsx [app-client] (ecmascript) @ Providers.tsx:8
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateModuleFromParent @ dev-base.ts:126
commonJsRequire @ runtime-utils.ts:291
requireModule @ react-server-dom-turbopack-client.browser.development.js:97
initializeModuleChunk @ react-server-dom-turbopack-client.browser.development.js:1126
readChunk @ react-server-dom-turbopack-client.browser.development.js:931
react_stack_bottom_frame @ react-dom-client.development.js:23659
beginWork @ react-dom-client.development.js:10605
runWithFiberInDEV @ react-dom-client.development.js:872
performUnitOfWork @ react-dom-client.development.js:15677
workLoopConcurrentByScheduler @ react-dom-client.development.js:15671
renderRootConcurrent @ react-dom-client.development.js:15646
performWorkOnRoot @ react-dom-client.development.js:14940
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16766
performWorkUntilDeadline @ scheduler.development.js:45
"use client"
RootLayout @ layout.tsx:101
initializeElement @ react-server-dom-turbopack-client.browser.development.js:1200
(anonymous) @ react-server-dom-turbopack-client.browser.development.js:2823
initializeModelChunk @ react-server-dom-turbopack-client.browser.development.js:1102
readChunk @ react-server-dom-turbopack-client.browser.development.js:928
react_stack_bottom_frame @ react-dom-client.development.js:23659
createChild @ react-dom-client.development.js:5464
reconcileChildrenArray @ react-dom-client.development.js:5771
reconcileChildFibersImpl @ react-dom-client.development.js:6094
(anonymous) @ react-dom-client.development.js:6199
reconcileChildren @ react-dom-client.development.js:8753
beginWork @ react-dom-client.development.js:10878
runWithFiberInDEV @ react-dom-client.development.js:872
performUnitOfWork @ react-dom-client.development.js:15677
workLoopConcurrentByScheduler @ react-dom-client.development.js:15671
renderRootConcurrent @ react-dom-client.development.js:15646
performWorkOnRoot @ react-dom-client.development.js:14940
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16766
performWorkUntilDeadline @ scheduler.development.js:45
<RootLayout>
initializeFakeTask @ react-server-dom-turbopack-client.browser.development.js:2401
resolveDebugInfo @ react-server-dom-turbopack-client.browser.development.js:2426
processFullStringRow @ react-server-dom-turbopack-client.browser.development.js:2627
processFullBinaryRow @ react-server-dom-turbopack-client.browser.development.js:2599
processBinaryChunk @ react-server-dom-turbopack-client.browser.development.js:2726
progress @ react-server-dom-turbopack-client.browser.development.js:2990
"use server"
ResponseInstance @ react-server-dom-turbopack-client.browser.development.js:1863
createResponseFromOptions @ react-server-dom-turbopack-client.browser.development.js:2851
exports.createFromReadableStream @ react-server-dom-turbopack-client.browser.development.js:3213
[project]/node_modules/next/dist/client/app-index.js [app-client] (ecmascript) @ app-index.tsx:157
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateModuleFromParent @ dev-base.ts:126
commonJsRequire @ runtime-utils.ts:291
(anonymous) @ app-next-turbopack.ts:11
(anonymous) @ app-bootstrap.ts:78
loadScriptsInSequence @ app-bootstrap.ts:20
appBootstrap @ app-bootstrap.ts:60
[project]/node_modules/next/dist/client/app-next-turbopack.js [app-client] (ecmascript) @ app-next-turbopack.ts:10
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateRuntimeModule @ dev-base.ts:96
registerChunk @ runtime-backend-dom.ts:88
await in registerChunk
registerChunk @ runtime-base.ts:377
(anonymous) @ dev-backend-dom.ts:126
(anonymous) @ dev-backend-dom.ts:126Understand this error
FetchUtil.ts:20 Fetch API cannot load https://api.web3modal.org/appkit/v1/config?projectId=54848d4e8a3a1da71c0400f011bfc230&st=appkit&sv=html-core-1.7.8. Refused to connect because it violates the document's Content Security Policy.
fetchData @ FetchUtil.ts:20
get @ FetchUtil.ts:44
fetchProjectConfig @ ApiController.ts:158
fetchRemoteFeatures @ ConfigUtil.ts:233
initialize @ appkit-base-client.ts:165
await in initialize
AppKitBaseClient @ appkit-base-client.ts:142
AppKit @ appkit-core.ts:34
createAppKit @ core.ts:12
initialize @ browser.js:8
await in initialize
init @ browser.js:8
initProvider @ walletConnect.ts:251
await in initProvider
getProvider @ walletConnect.ts:270
setup @ walletConnect.ts:118
setup @ createConfig.ts:107
(anonymous) @ createConfig.ts:71
createStoreImpl @ vanilla.mjs:19
createStore @ vanilla.mjs:22
createConfig @ createConfig.ts:67
[project]/src/lib/wagmi.ts [app-client] (ecmascript) @ wagmi.ts:5
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateModuleFromParent @ dev-base.ts:126
esmImport @ runtime-utils.ts:264
[project]/src/app/components/Providers.tsx [app-client] (ecmascript) @ Providers.tsx:8
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateModuleFromParent @ dev-base.ts:126
commonJsRequire @ runtime-utils.ts:291
requireModule @ react-server-dom-turbopack-client.browser.development.js:97
initializeModuleChunk @ react-server-dom-turbopack-client.browser.development.js:1126
readChunk @ react-server-dom-turbopack-client.browser.development.js:931
react_stack_bottom_frame @ react-dom-client.development.js:23659
beginWork @ react-dom-client.development.js:10605
runWithFiberInDEV @ react-dom-client.development.js:872
performUnitOfWork @ react-dom-client.development.js:15677
workLoopConcurrentByScheduler @ react-dom-client.development.js:15671
renderRootConcurrent @ react-dom-client.development.js:15646
performWorkOnRoot @ react-dom-client.development.js:14940
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16766
performWorkUntilDeadline @ scheduler.development.js:45
"use client"
RootLayout @ layout.tsx:101
initializeElement @ react-server-dom-turbopack-client.browser.development.js:1200
(anonymous) @ react-server-dom-turbopack-client.browser.development.js:2823
initializeModelChunk @ react-server-dom-turbopack-client.browser.development.js:1102
readChunk @ react-server-dom-turbopack-client.browser.development.js:928
react_stack_bottom_frame @ react-dom-client.development.js:23659
createChild @ react-dom-client.development.js:5464
reconcileChildrenArray @ react-dom-client.development.js:5771
reconcileChildFibersImpl @ react-dom-client.development.js:6094
(anonymous) @ react-dom-client.development.js:6199
reconcileChildren @ react-dom-client.development.js:8753
beginWork @ react-dom-client.development.js:10878
runWithFiberInDEV @ react-dom-client.development.js:872
performUnitOfWork @ react-dom-client.development.js:15677
workLoopConcurrentByScheduler @ react-dom-client.development.js:15671
renderRootConcurrent @ react-dom-client.development.js:15646
performWorkOnRoot @ react-dom-client.development.js:14940
performWorkOnRootViaSchedulerTask @ react-dom-client.development.js:16766
performWorkUntilDeadline @ scheduler.development.js:45
<RootLayout>
initializeFakeTask @ react-server-dom-turbopack-client.browser.development.js:2401
resolveDebugInfo @ react-server-dom-turbopack-client.browser.development.js:2426
processFullStringRow @ react-server-dom-turbopack-client.browser.development.js:2627
processFullBinaryRow @ react-server-dom-turbopack-client.browser.development.js:2599
processBinaryChunk @ react-server-dom-turbopack-client.browser.development.js:2726
progress @ react-server-dom-turbopack-client.browser.development.js:2990
"use server"
ResponseInstance @ react-server-dom-turbopack-client.browser.development.js:1863
createResponseFromOptions @ react-server-dom-turbopack-client.browser.development.js:2851
exports.createFromReadableStream @ react-server-dom-turbopack-client.browser.development.js:3213
[project]/node_modules/next/dist/client/app-index.js [app-client] (ecmascript) @ app-index.tsx:157
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateModuleFromParent @ dev-base.ts:126
commonJsRequire @ runtime-utils.ts:291
(anonymous) @ app-next-turbopack.ts:11
(anonymous) @ app-bootstrap.ts:78
loadScriptsInSequence @ app-bootstrap.ts:20
appBootstrap @ app-bootstrap.ts:60
[project]/node_modules/next/dist/client/app-next-turbopack.js [app-client] (ecmascript) @ app-next-turbopack.ts:10
(anonymous) @ dev-base.ts:201
runModuleExecutionHooks @ dev-base.ts:256
instantiateModule @ dev-base.ts:199
getOrInstantiateRuntimeModule @ dev-base.ts:96
registerChunk @ runtime-backend-dom.ts:88
await in registerChunk
registerChunk @ runtime-base.ts:377
(anonymous) @ dev-backend-dom.ts:126
(anonymous) @ dev-backend-dom.ts:126Understand this error
ConfigUtil.ts:236 [Reown Config] Failed to fetch remote project configuration. Using local/default values. TypeError: Failed to fetch. Refused to connect because it violates the document's Content Security Policy.
    at fetchData (FetchUtil.ts:20:26)
    at FetchUtil.get (FetchUtil.ts:44:28)
    at Object.fetchProjectConfig (ApiController.ts:158:32)
    at Object.fetchRemoteFeatures (ConfigUtil.ts:233:46)
    at AppKit.initialize (appkit-base-client.ts:165:44)