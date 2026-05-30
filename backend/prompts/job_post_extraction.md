Extract job posting data from rendered page text.

Return only a valid JSON object with this shape:

{
  "company_name": string | null,
  "position_title": string | null,
  "position_description": string | null,
  "location": string | null,
  "remote_policy": string | null,
  "seniority": string | null,
  "employment_type": string | null,
  "salary": string | null,
  "contact_url": string | null,
  "contact_description": string | null,
  "recruitment_description": string | null,
  "tags": [
    {
      "name": string,
      "kind": string,
      "confidence": number | null,
      "source": "codex"
    }
  ]
}

Use only facts present or strongly implied by the text. Tags should include technologies,
frameworks, clouds, databases, architecture terms, methodologies, domains, and hiring
buzzwords. For seniority, use exactly one of these values when it fits the posting:
Middle Developer, Senior Developer, Principal Developer, Middle Data Engineer,
Senior Data Engineer, Principal Data Engineer, Software Architect, Data Architect,
Middle Manager, Senior Manager. Use null for unknown scalar fields and [] for no tags.

For contact_url: extract a direct link to the recruiter/hiring manager profile (LinkedIn, etc.) if present.
For contact_description: extract recruiter name, title, or any contact instructions mentioned.
For recruitment_description: extract the hiring process steps, interview stages, timeline, or any process description.
