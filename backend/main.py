from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from lark import UnexpectedInput
from typing import List

from processing import formula_to_dot  # <- now expects (formula, variable_order)

app = FastAPI()

class FormulaRequest(BaseModel):
    formula: str
    variable_order: List[str] = []

@app.post("/automaton/dot")
async def automaton_dot(req: FormulaRequest):
    formula = req.formula
    variable_order = req.variable_order
    try:
        variables, dot_string = formula_to_dot(formula, variable_order)
        print(variables)
    except UnexpectedInput as exc:
        try:
            context = exc.get_context(formula)
        except Exception:
            context = str(exc)
        return Response(
            content="Syntax error:\n" + context,
            media_type="text/plain",
            status_code=400,
        )
    except AssertionError as exc:
        return Response(
            content="Syntax error:\n" + str(exc),
            media_type="text/plain",
            status_code=400,
        )

    return JSONResponse(
        content={
            "dot": dot_string,
            "variables": variables,
        }
    )