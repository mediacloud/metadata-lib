Version History
===============

Version 1
---------

### v1.0.0
* small dependency updates
* changed version management system
* first release packaged with Flit


Version 0
---------

* __v0.12.0__: Add new const to centrally store MC User-Agent (`mcmetadata.webpages.MEDIA_CLOUD_USER_AGENT`)
* __v0.11.2__: Fix title parsing and url normalization edge cases, update requirements
* __v0.11.1__: Add new `urls.unique_url_hash` helper to centralize logic for generating a unique hash for a URL, also
               returned from `extract` in case you choose to use it
* __v0.11.0__: (error release)
* __v0.10.0__: Support defaults and overrides in `extract`, returning execution time stats, requirements updates, more
               handling of malformed URLs
* __v0.9.5__: Updated requirements, update non-news site list, fix failing unit tests, tweak title parsing logic
* __v0.9.4__: Updated requirements to use faust-cchardet for py >3.9 support
* __v0.9.3__: Updated content extractor dependencies, added py.typing for typing support
* __v0.9.2__: fixed a bug related to title regex matching
* __v0.9.1__: better support for some non-US government domains
* __v0.9.0__: adds `feeds.normalize_url` helper
* __v0.8.2__: small fix to url parsing
* __v0.8.1__: handle IP addresses in canonical_domain helper
* __v0.8.0__: update dependencies, fix various edge-case bugs
* __v0.7.9__: fix `include_other_metadata` processing, upgrade underlying libraries to latest, remove leading and
              trailing whitespace from extracted text
* __v0.7.8__: add optional `include_other_metadata` arg to extract method, which includes top_image and authors and
              other less validated metadata in results
* __v0.7.7__: fix typo
* __v0.7.6__: fix distribution packaging error
* __v0.7.5__: add performance monitoring, handle invalid URLs, add a list of high volume non-news domains that might be
              worth ignoring (based on high volume "noise" domains in our production database)
* __v0.7.4__: don't treat shortened URLs as homepage ones, also more aggressively strip URL query params
* __v0.7.3__: tweak title extraction for multipart titles, add is_homepage helper boolean
* __v0.7.2__: fix extraction argument bug introduced in last release, fix some more test cases
* __v0.7.1__: fix bug in url normalization, increase robustness in extractor chain
* __v0.7.0__: fix YouTube url normalization, better Trafilatura defaults, limit to pub dates within 90 days of today,
              ensure language is 2 letters, content extraction performance improvements, fix some title parsing bugs,
              add more test cases, add script to compare results to older Media Cloud code (which this stuff is
              extracted from), resolve language guessing conflicts better, handle text encoding errors
* __v0.6.0__: prefer language from metadata over guessing, try Trafilatura as first parser, encoding fixes
* __v0.5.5__: turn off aggressive date finding mode, which was making lots of 1/1 date guesses
* __v0.5.4__: bug in regex that parses og:title properties into titles
* __v0.5.3__: bug fixes in title normalization
* __v0.5.2__: more efficient parsing of dates from HTML, remove failing over-specified canonical domain case
* __v0.5.1__: fix small bug related to use of BeautifulSoup
* __v0.5.0__: add normalized URL and normalized title
* __v0.4.3__: *more* work on title regex bug
* __v0.4.2__: work on title regex bug
* __v0.4.1__: work on deployment
* __v0.4.0__: performance improvements, dependency updates
* __v0.3.1__: update dependencies
* __v0.3.0__: more fault tolerant, faster regex's, track extraction rates, update requirements
* __v0.2.0__: first packaging release for use in other places
* __v0.1.1__: first version for testing with collaborators
