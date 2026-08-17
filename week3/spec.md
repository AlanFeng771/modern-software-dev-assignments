# Week 3 — MCP Server Spec: GitHub Repository Explorer

External API: GitHub REST API (`api.github.com`)
Deployment mode: Local (STDIO) first, extend to Remote (HTTP) later for extra credit
Usage flow: User asks "any good repos for XXX?" → model calls Tool 1 to get a candidate list → user/model picks one → model calls Tool 2 to get detailed info about it

---

## Tool 1: `get_useful_repositories`

**Description:**
> Lists GitHub repositories matching a given `keyword`, including a short description, plus the repository's `owner` and `repo`, which can be passed to `get_repository_info` for detailed information.

**Input Schema**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keyword` | str | required | Keyword to search for repositories |
| `max_repository_output` | int | optional (default 10) | Maximum number of repositories to return |

**GitHub API Endpoint**
`GET https://api.github.com/search/repositories`
Query: `q={keyword}`, `sort=stars`, `order=desc`  

**Output (success)**
```json
{
  "items": [
    {"owner": "string", "repo": "string", "description": "string", "stars": 0}
  ]
}
```

**Error Handling**

| Condition | Response |
|---|---|
| Invalid search query (`422 Validation Failed`) | "Your search keyword could not be processed. Please try a simpler or different keyword." |
| Search API rate limit exceeded (`403`, `X-RateLimit-Remaining: 0`) | "GitHub Search API rate limit exceeded. Please try again in approximately {N} minute(s)." |
| No matching repositories (`items` is empty) | "No repositories found matching `{keyword}`." |
| Request timeout | "The request to GitHub timed out. Please try again." |
| Network / connection error | "Could not reach GitHub API. Please check your network connection." |
| `503 Service Unavailable` | "GitHub API is temporarily unavailable. Please try again later." |

---

## Tool 2: `get_repository_info`

**Description:**
> Retrieves general information about a GitHub repository, including its description, primary language, license, star/fork counts, and topics — useful for understanding what a project is and how active it is.

**Input Schema**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `owner` | str | required | The GitHub username or organization that owns the repository |
| `repo` | str | required | The repository name |

**GitHub API Endpoint**
`GET https://api.github.com/repos/{owner}/{repo}`

**Output (success)**
```json
{
  "description": "string",
  "stargazers_count": 0,
  "open_issues_count": 0,
  "language": "string",
  "forks_count": 0,
  "topics": ["string"],
  "html_url": "string"
}
```

**Error Handling**

| Condition | Response |
|---|---|
| Repository not found (`404`) | "Could not find repository `{owner}/{repo}`. Please check the owner and repo name." |
| Core API rate limit exceeded (`403`, `X-RateLimit-Remaining: 0`) | "GitHub API rate limit exceeded. Please try again in approximately {N} minute(s)." |
| `description` is `null` | Return `"No description provided."` instead of `null` |
| Request timeout | "The request to GitHub timed out. Please try again." |
| Network / connection error | "Could not reach GitHub API. Please check your network connection." |
| `503 Service Unavailable` | "GitHub API is temporarily unavailable. Please try again later." |

---

## Key Design Decisions (with rationale)

- **Division of labor between the two tools**: Tool 1 handles "discovery" (keyword → candidate list), Tool 2 handles "deep dive" (owner/repo → detailed info). Tool 1's output deliberately includes `owner`/`repo` so it can be fed directly into Tool 2, forming a chained workflow.
- **Ranking criterion**: Tool 1 uses `sort=stars` (star count as the signal for "good"), so the output must include the `stars` field — this lets the model explain *why* a repo is being recommended without an extra call to Tool 2.
- **Keyword extraction is the model's responsibility, not the tool's**: The tool only defines a `keyword: str` input parameter; it does not perform any NLP/keyword extraction internally. The model reads the user's conversation and decides how to fill the parameter — this follows MCP's division of responsibility (the model decides *whether* and *how* to call a tool; the tool only executes the action).
- **Rate limit handling strategy**: Don't proactively call `/rate_limit` on every request (wastes quota) — instead passively read `X-RateLimit-Remaining` / `X-RateLimit-Reset` from each API response's headers, and only surface a warning when the quota is actually exhausted (403). The server never sleeps to wait for the reset — since tool calls are synchronous, it should immediately report "how long to wait" and let the caller decide, rather than blocking.
- **Search API and Core API have separate rate-limit buckets**: The Search API (`/search/*`) has a much stricter unauthenticated limit (10 req/min) than the Core API (60 req/hour). Both tools must handle their own bucket's limit — the same header-reading logic works for both, since GitHub automatically returns the correct bucket's info for whichever endpoint was called.
- **404 vs. 422**: `/repos/{owner}/{repo}` treats owner/repo as a path parameter, so a nonexistent repo returns 404. `/search/*` treats the query as a filter, so an invalid/nonexistent target in the query returns 422 instead (verified empirically). The two endpoints cannot share the same error-handling logic.
- **304 is not handled**: No ETag/conditional-request caching is implemented (out of scope for this assignment), so 304 cannot occur under the current design and is therefore excluded from error handling.
