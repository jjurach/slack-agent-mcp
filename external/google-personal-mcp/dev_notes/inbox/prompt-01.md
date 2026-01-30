Create a project plan to integrate imported docs/system-prompts into this project.

Read docs/system-prompts/README.md for more information.

I applied `./docs/system-prompts/bootstrap.py --commit` with this output:
```
Initializing new /home/phaedrus/AiSpace/google-personal-mcp/AGENTS.md
✓ Updated section: CORE-WORKFLOW
✓ Updated section: PRINCIPLES
✓ Updated section: PYTHON-DOD
✓ Wrote: /home/phaedrus/AiSpace/google-personal-mcp/docs/workflows.md
✓ Wrote: /home/phaedrus/AiSpace/google-personal-mcp/AIDER.md
✓ Wrote: /home/phaedrus/AiSpace/google-personal-mcp/CLAUDE.md
✓ Wrote: /home/phaedrus/AiSpace/google-personal-mcp/CLINE.md
✓ Wrote: /home/phaedrus/AiSpace/google-personal-mcp/GEMINI.md
✓ Wrote: /home/phaedrus/AiSpace/google-personal-mcp/AGENTS.md

✓ Successfully synced /home/phaedrus/AiSpace/google-personal-mcp/AGENTS.md

⚠️  Gaps (TODOs) found in the following files:
   - /home/phaedrus/AiSpace/google-personal-mcp/AGENTS.md
   - /home/phaedrus/AiSpace/google-personal-mcp/docs/definition-of-done.md
   - /home/phaedrus/AiSpace/google-personal-mcp/docs/workflows.md
```

The project plan should do these things:

- review all .md files and consider these potential problems:
  - evalute all TODOs to fill the gaps.
  - apply whatever available integrity processes and address any important issues which will block an agent from understanding
  - reduce repetition:  consider moving good, generic, agent-agnostic advice out of docs/ proper and into docs/system-prompts
    - leave any information which is specific to mcp servers or google api's etc in docs/ proper, but
    - improve docs/system-prompts with good practice which can apply to other projects.

When good advice is refactored out of docs/definition-of-done.md into system-prompts, make sure that AGENTS.md docs/definition-of-done.md docs/system-prompts/principals/definition-of-done.md are all linked together and accessible to general agent context.

Create this project plan.
