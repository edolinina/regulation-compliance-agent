from pathlib import Path


REGULATION_PDFS = {
    "C194": (
        "https://www.cysec.gov.cy/CMSPages/GetFile.aspx"
        "?guid=941acdaa-0e78-44b2-853e-14007451d7e8"
    ),
    "C181": (
        "https://www.cysec.gov.cy/CMSPages/GetFile.aspx"
        "?guid=ea02458e-f564-4ec1-ab4d-79a32fb76705"
    ),
    "CI144-2012-10": (
        "https://www.cysec.gov.cy/CMSPages/GetFile.aspx"
        "?guid=959f2de5-e987-4041-94bc-ca5e1283fc97"
    ),
    "C502": (
        "https://www.cysec.gov.cy/CMSPages/GetFile.aspx"
        "?guid=ddc8f60a-6b6e-4959-96bf-f74909d76988"
    ),
    "ESMA35-36-1743": (
        "https://www.esma.europa.eu/sites/default/files/library/"
        "esma35-36-1743-statement_product_intervention.pdf"
    ),
    "ESMA35-43-1000": (
        "https://www.esma.europa.eu/sites/default/files/library/"
        "esma35-43-1000_additional_information_on_the_agreed_"
        "product_intervention_measures_relating_to_contracts_"
        "for_differences_and_binary_options.pdf"
    ),
}

DATA_DIR = Path("data")
PDF_DIR = DATA_DIR / "pdfs"
RULES_PATH = DATA_DIR / "rules.json"

DEFAULT_MODEL = "gpt-4.1-mini"
DOWNLOAD_TIMEOUT_SECONDS = 60
MAX_CONCURRENT_DOCUMENTS = 3

EXTRACTION_SYSTEM_PROMPT = """
You extract compliance rules from regulatory circulars.

Extract only rules that can be checked against:
- marketing materials;
- promotions;
- client communications;
- bonuses, rewards, or financial incentives.

Each rule must:
- represent one atomic obligation or prohibition;
- be directly supported by the circular;
- be checkable against user-provided text;
- include the source page;
- include a short supporting quote.

Do not extract:
- background information;
- regulatory history;
- general summaries;
- administrative instructions unrelated to marketing;
- requirements that cannot be checked against user-provided marketing text.

Always leave `source_url` empty.

It is valid to return an empty rules list.

Use rule IDs in this format:
{document_id}-R001
{document_id}-R002
"""

EXTRACTION_USER_PROMPT = """
Document ID: {document_id}

Circular text:

{document_text}
"""

EVALUATION_SYSTEM_PROMPT = """
Evaluate the user text against every supplied compliance rule.

Return only compliance failures.

Report a failure only when:
- the rule directly applies to the supplied text;
- the violating wording can be quoted as evidence;
- the violation does not depend solely on assuming omitted information is missing.

Do not report failures based only on missing information. Report omissions only when the supplied text contains a claim that requires the missing information under the applicable rule.

For every failure provide:
- rule_id: the ID of the violated rule;
- title: short user-facing issue name (max 6 words);
- evidence: the shortest relevant phrase from the user text;
- explanation: one short sentence;
- recommendation: one short actionable sentence.

Do not:
- return passing or non-applicable rules;
- repeat the regulation;
- provide legal background;
- produce lengthy reasoning;
- duplicate the same issue;
- invent evidence;
- treat a positive statement as unbalanced unless it exaggerates, guarantees, conceals, or materially misrepresents a risk, cost, or limitation.

If there are no failures, return an empty failures list.
"""

EVALUATION_USER_PROMPT = """
Marketing text:
{user_text}

Compliance rules:
{rules}

Return only the rules that the text violates.
"""
