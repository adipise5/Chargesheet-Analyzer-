# Deployment snapshot sources

The deployment snapshot contains six case workspaces: one educational sample
chargesheet and five separate public-judgment source cases. Each judgment case
contains the original public judgment as its only case document, so it is an
incomplete source set rather than a complete chargesheet, live police record,
or linked investigation. The same five judgments are also available in the
Precedents corpus.

The snapshot does not contain any private records supplied during local
testing. The educational sample is not a real prosecution.

## Public source documents

- Educational final investigation report: https://www.lawctopus.com/wp-content/uploads/2014/09/Chargesheet.pdf
- Sharif Ahmad v. State of Uttar Pradesh: https://indiankanoon.org/doc/13608821/
- Msusha Kant Asiwal v. GNCTD: https://indiankanoon.org/doc/132151361/?type=print
- Sajid v. State: https://indiankanoon.org/doc/108013980/
- Subhash Chandra v. State of Uttar Pradesh: https://indiankanoon.org/doc/137438498/
- Honnaiah T.H. v. State of Karnataka: https://indiankanoon.org/doc/6802571/

The four eCourts links in the supplied list were checked during staging and
returned HTTP 404 responses. They are recorded as unavailable in
`demo_snapshot/public_source_report.json` and are not imported from error
pages. The repeatable catalog is `scripts/public_demo_sources.json`.

## Demonstration limits

- The five judgment cases are reference examples and are excluded from
  incident-oriented seasonality, hotspots, and crime statistics by default.
  Use the visible analytics scope control only when you intentionally want to
  inspect them alongside incident-style records.
- The six records are a demonstration corpus, not crime statistics. Extraction
  counts describe the uploaded record, not verified crime statistics.
- Missing supporting documents mean they were not uploaded; this does not
  establish that investigators lack those documents.
- English is the default demonstration language. Cached Gujarati model
  translations have incomplete coverage and require fluent human review.
- Ask Case has four prepared questions plus keyword/graph source retrieval.
  Arbitrary questions return excerpts, not newly generated model answers.
- The source text and citations remain the authority for reviewing generated
  summaries, findings, and judgment synthesis.

## Rebuilding the snapshot

Run `scripts/import_public_demo.py --replace` from the normal local environment
after the local Ollama models are available. The importer validates the tracked
public artifacts, stages a sibling workspace outside `data/`, processes each
public judgment once, warms the reusable outputs and translations, and exports
the audited result into `demo_snapshot/`. It never downloads sources when the
app starts. Review the generated manifest, source report, privacy scan, and Git
diff before force-adding the ignored snapshot directory.
