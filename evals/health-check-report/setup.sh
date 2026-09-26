#!/usr/bin/env bash
# Build the shared test brain (a fictional company) in the run's empty workspace.
set -euo pipefail
python3 "$(cd "$(dirname "$0")" && pwd)/../_fixtures/make_brain.py" ./business-brain
python3 - <<'PY'
import os
def w(domain, eid, meta, body):
    m={"id":eid,"domain":domain,"status":"active","source_type":"internal-document","recorded_on":"2026-06-01","review_by":"2027-06-01","confidence":"high","sensitivity":"internal"}; m.update(meta)
    p=f"business-brain/entries/{domain}/{eid}.md"; os.makedirs(os.path.dirname(p),exist_ok=True)
    open(p,"w").write("---\n"+"\n".join(f"{k}: {v}" for k,v in m.items() if v is not None)+"\n---\n\n"+body+"\n")

w("policies","policies-refund-faq",{"title":"Refund period (website FAQ)","type":"policy","key":"policy.refund.window-days","value":"30 days","source":"Website FAQ, August 2026","confidence":"medium","sensitivity":"public"},"The website FAQ promises a 30-day money-back guarantee.")
w("policies","policies-late-fee",{"title":"Late payment fee","type":"policy","key":"policy.payment.late-fee","value":"2% per month","source":"Terms of service v4","review_by":"2026-03-01"},"Overdue invoices incur a late fee of 2% per month.")
w("procedures","procedures-onboarding-call",{"title":"Onboarding call","type":"procedure","source":None},"Every new customer gets a 30-minute onboarding call in their first week.")
PY
