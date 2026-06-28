# Marks the `prompts` folder as a Python package.
#
# Phase 7: prompt templates for the optional Claude-powered RAG answers. The
# system prompt here is the safety boundary — it forbids accusations, keeps the
# model to retrieved context, and defends against prompt injection from OCR text
# and reviewer questions (both treated as UNTRUSTED data, never instructions).
