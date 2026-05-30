import google.generativeai as genai
import json
import re


SYSTEM_PROMPT = """You are an expert SQL analyst AI. Your job is to:
1. Convert natural language questions into accurate, optimized SQL queries
2. Suggest the best chart type for the data
3. Provide a brief plain-English explanation of what the query does

You are connected to a database with the following schema:
{schema}

Rules:
- Always return valid SQL for the detected dialect (default: SQLite/PostgreSQL compatible)
- Use proper JOINs, aggregations, GROUP BY, ORDER BY as needed
- For date/time queries, use appropriate date functions
- Limit results to 1000 rows max unless asked for more
- Never use DROP, DELETE, UPDATE, INSERT, or any destructive SQL
- Always alias aggregated columns clearly (e.g. AS total_revenue)

Return your response as a JSON object with these exact fields:
{{
  "sql": "SELECT ...",
  "explanation": "This query...",
  "chart_type": "line|bar|pie|scatter|area|table|heatmap",
  "chart_hint": "brief note about what to visualize"
}}

Chart type guide:
- line: trends over time, time series
- bar: comparisons between categories
- pie: proportions, market share (max 8 categories)
- scatter: correlations between two numeric variables
- area: cumulative trends
- heatmap: two-dimensional comparisons
- table: detailed records, text-heavy data

Only return the JSON object — no markdown, no explanation outside the JSON.
"""


class AIEngine:
    def __init__(self, api_key: str, model: str, schema: dict):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=1500,
            ),
        )
        self.schema = schema

    def _format_schema(self) -> str:
        lines = []
        for table, cols in self.schema.items():
            col_defs = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
            lines.append(f"Table: {table}\n  Columns: {col_defs}")
        return "\n\n".join(lines)

    def process_query(self, user_question: str) -> dict:
        schema_str = self._format_schema()
        prompt = SYSTEM_PROMPT.format(schema=schema_str) + f"\n\nUser question: {user_question}"

        response = self.model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)

        # Validate required fields
        if "sql" not in result:
            raise ValueError("AI did not return a SQL query.")

        # Safety check — block destructive SQL
        dangerous = ["drop ", "delete ", "update ", "insert ", "alter ", "truncate ", "create "]
        sql_lower = result["sql"].lower()
        for keyword in dangerous:
            if keyword in sql_lower:
                raise ValueError(f"Unsafe SQL detected (contains '{keyword.strip()}'). Only SELECT queries are allowed.")

        return result
