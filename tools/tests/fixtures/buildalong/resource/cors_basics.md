Cross-origin resource sharing (CORS) basics, invented summary for tests.
A browser sends an Origin header on cross-origin requests. A server answers with Access-Control-Allow-Origin.
Check 1: send a request with an Origin you control and see whether the same value is echoed back.
Check 2: if credentials are allowed (Access-Control-Allow-Credentials true), an echoed Origin lets another site read the response.
Check 3: the value null and sub-domain look-alikes are common mistakes in allow lists.
Indicators: the echoed origin changes with the request; a wildcard together with credentials is rejected by browsers.
Pitfall: a wildcard on a public, unauthenticated resource is not a finding.
