#!/usr/bin/env python3
"""Search the second brain with a local Ollama model (RAG-lite).

Usage: python3 search.py "your question about the vault"
Ensures `ollama serve` is running, retrieves the most relevant notes,
and asks the model to answer using only those notes.
"""
import sys
import textwrap
import sb_lib as sb


def main():
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print("Usage: search.py <question>")
        return 2

    if not sb.ensure_ollama():
        print("ERROR: could not reach or start `ollama serve` on "
              f"{sb.OLLAMA_HOST}. Is ollama installed?")
        return 1
    if not sb.model_available():
        print(f"ERROR: model '{sb.MODEL}' not found. Pull it with: "
              f"ollama pull {sb.MODEL}")
        return 1

    hits = sb.retrieve(query, k=6)
    if not hits:
        print(f"No notes in {sb.VAULT} matched: {query}")
        return 0

    # Build a bounded context window from the top notes.
    blocks, budget = [], 12000
    for score, path, text in hits:
        rel = path.relative_to(sb.VAULT)
        snippet = text[: min(len(text), 3000)]
        block = f"### NOTE: {rel}\n{snippet}\n"
        if budget - len(block) < 0:
            break
        blocks.append(block)
        budget -= len(block)

    context = "\n".join(blocks)
    prompt = textwrap.dedent(f"""\
        You are a retrieval assistant for a personal Obsidian "second brain".
        Answer the QUESTION using ONLY the NOTES below. Be concise and concrete.
        Cite the note filenames you used in a "Sources:" line. If the notes do
        not contain the answer, say so plainly.

        QUESTION: {query}

        NOTES:
        {context}
    """)

    answer = sb.ollama_generate(prompt, num_predict=900)
    print(answer)
    print("\n— retrieved from —")
    for score, path, _ in hits:
        print(f"  • {path.relative_to(sb.VAULT)}  (score {score})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
