[Reown Config] Failed to fetch remote project configuration. Using local/default values. Error: HTTP status code: 403
    at d (.next/server/chunks/7159.js:48:68579)
    at async e.get (.next/server/chunks/7159.js:48:68805)
    at async Object.fetchProjectConfig (.next/server/chunks/7159.js:937:7970)
    at async Object.fetchRemoteFeatures (.next/server/chunks/7159.js:27:213831)
    at async jO.initialize (.next/server/chunks/7159.js:27:218644) {
  [cause]: Response {
    status: 403,
    statusText: 'Forbidden',
    headers: Headers {
      date: 'Tue, 12 Aug 2025 02:04:50 GMT',
      'content-type': 'text/plain; charset=UTF-8',
      'content-length': '9',
      connection: 'keep-alive',
      'cf-ray': '96dc677c9ce891fa-IAD',
      'access-control-allow-origin': '*',


 ⨯ useSearchParams() should be wrapped in a suspense boundary at page "/login". Read more: https://nextjs.org/docs/messages/missing-suspense-with-csr-bailout
    at g (/vercel/path0/4ex.ninja-frontend/.next/server/chunks/6686.js:9:73268)
    at l (/vercel/path0/4ex.ninja-frontend/.next/server/chunks/6686.js:17:20466)
    at h (/vercel/path0/4ex.ninja-frontend/.next/server/app/login/page.js:2:7882)
    at n4 (/vercel/path0/4ex.ninja-frontend/node_modules/next/dist/compiled/next-server/app-page.runtime.prod.js:2:81697)
    at n8 (/vercel/path0/4ex.ninja-frontend/node_modules/next/dist/compiled/next-server/app-page.runtime.prod.js:2:83467)
    at n9 (/vercel/path0/4ex.ninja-frontend/node_modules/next/dist/compiled/next-server/app-page.runtime.prod.js:2:103676)
    at n5 (/vercel/path0/4ex.ninja-frontend/node_modules/next/dist/compiled/next-server/app-page.runtime.prod.js:2:101094)
    at n3 (/vercel/path0/4ex.ninja-frontend/node_modules/next/dist/compiled/next-server/app-page.runtime.prod.js:2:82049)
    at n8 (/vercel/path0/4ex.ninja-frontend/node_modules/next/dist/compiled/next-server/app-page.runtime.prod.js:2:83513)
    at n8 (/vercel/path0/4ex.ninja-frontend/node_modules/next/dist/compiled/next-server/app-page.runtime.prod.js:2:100435)
Error occurred prerendering page "/login". Read more: https://nextjs.org/docs/messages/prerender-error
Export encountered an error on /login/page: /login, exiting the build.
 ⨯ Next.js build worker exited with code: 1 and signal: null
Error: Command "npm run vercel-build" exited with 1