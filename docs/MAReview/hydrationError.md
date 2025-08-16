Error: Hydration failed because the server rendered HTML didn't match the client. As a result this tree will be regenerated on the client. This can happen if a SSR-ed Client Component used:

- A server/client branch `if (typeof window !== 'undefined')`.
- Variable input such as `Date.now()` or `Math.random()` which changes each time it's called.
- Date formatting in a user's locale which doesn't match the server.
- External changing data without sending a snapshot of it along with the HTML.
- Invalid HTML tag nesting.

It can also happen if the client has a browser extension installed which messes with the HTML before React loaded.

https://react.dev/link/hydration-mismatch

  ...
    <ErrorBoundary errorComponent={undefined} errorStyles={undefined} errorScripts={undefined}>
      <LoadingBoundary loading={null}>
        <HTTPAccessFallbackBoundary notFound={undefined} forbidden={undefined} unauthorized={undefined}>
          <RedirectBoundary>
            <RedirectErrorBoundary router={{...}}>
              <InnerLayoutRouter url="/regime-mo..." tree={[...]} cacheNode={{lazyData:null, ...}} segmentPath={[...]}>
                <ClientPageRoot Component={function RegimeMonitoringPage} searchParams={{}} params={{}}>
                  <RegimeMonitoringPage params={Promise} searchParams={Promise}>
                    <div className="min-h-scre...">
                      <div className="border-b b...">
                        <div className="max-w-7xl ...">
                          <div className="flex items...">
                            <div>
                            <div className="flex items...">
+                             <button
+                               onClick={function useRegimeData.useCallback[fetchData]}
+                               disabled={true}
+                               className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-neutral-600 r..."
+                             >
-                             <div className="px-3 py-1.5 text-sm bg-neutral-600 rounded">
                      ...
                ...

    at throwOnHydrationMismatch (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:2891:56)
    at beginWork (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:6089:918)
    at runWithFiberInDEV (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:890:74)
    at performUnitOfWork (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:8236:97)
    at workLoopConcurrentByScheduler (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:8232:58)
    at renderRootConcurrent (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:8214:71)
    at performWorkOnRoot (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:7846:176)
    at performWorkOnRootViaSchedulerTask (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_react-dom_1f56dc06._.js:8820:9)
    at MessagePort.performWorkUntilDeadline (http://localhost:3000/_next/static/chunks/node_modules_next_dist_compiled_0f1b9fd4._.js:2588:64)

    SyntaxError: Unexpected token '<', "<!DOCTYPE "... is not valid JSON