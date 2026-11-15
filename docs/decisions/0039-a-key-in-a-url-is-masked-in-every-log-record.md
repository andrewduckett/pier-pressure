---
id: adrs-adr0039
date: 2026-11-14
status: accepted
title: 'ADR-0039: A key that travels in a request URL is masked in every log record'
description: Architecture decision record for masking a service key that must travel in a request URL, such as a NASA FIRMS MAP_KEY, with a logging filter on every root handler, as well as never logging the errors that quote the URL.
---

# ADR-0039: A key that travels in a request URL is masked in every log record

## Context

Some data services take their key only in the URL path. NASA FIRMS is one: its
area API is `/api/area/csv/<key>/...`, with no header form. PierPressure logs at
INFO level, and its HTTP library, httpx, logs every request's full URL at INFO.
httpx's error messages quote the URL too, and the provider code logs a failed
fetch's error text. So a key in a URL reaches the log by at least two paths, and
a user who shares a log to ask for help shares the key with it.

## Decision

When the service holds a key that travels in a URL, it adds a logging filter to
every root handler. The filter replaces the key's text with a mask in each
record's message and exception text, whichever logger wrote it. The code that
makes the request also logs only a safe error description, never the error
itself, so the filter is a second guard and not the only one.

## Consequences

- **Easier:** no log line from any library, or from code written later, can
  carry the key, as long as it goes through `logging`.
- **Easier:** the request log for every other provider stays as it is.
- **Harder:** every log record pays for one text replacement while a key is set.
- **Harder:** the filter must be installed after logging is set up, and before
  the first request. A test has to cover that order.
- **Harder:** output that bypasses `logging`, such as a `print`, is not masked.

## Alternatives Considered

### Alternative 1: Raise the httpx logger to WARNING
- **Pros**: one line; the request log no longer prints any URL.
- **Cons**: removes the request log for every provider, which helps diagnose
  every other fetch. It does nothing for an error message that quotes the URL.
- **Why not**: it trades away a useful log for every provider, and still leaves
  the error path open.

### Alternative 2: Only log safe error descriptions at the call site
- **Pros**: no global logging change; each fetcher owns its safety.
- **Cons**: httpx's own INFO request line still carries the key, and any later
  code that logs an exception reopens the leak.
- **Why not**: it cannot stop a library's own log line, which is the leak that
  happens on every successful fetch.
