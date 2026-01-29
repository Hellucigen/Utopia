# Haru-AGI-prototype-system-incrementally-built-based-on-my-thesis.
This is a prototype AGI system incrementally developed with AI assistance, based on the thesis stored in my other repository. Below are demonstrations of the currently implemented features for each component:
main.py(There is currently an issue with the control of activation levels, which is awaiting a fix. Specifically, the application of activation levels is overly sensitive, and insufficient decay during a single inference run leads to residual activation artifacts):
Respond based on the knowledge graph:
<img width="1025" height="244" alt="QQ_1769696852087" src="https://github.com/user-attachments/assets/64361da6-441d-4a88-9146-9a0b1612f90d" />
<img width="1014" height="236" alt="QQ_1769696996789" src="https://github.com/user-attachments/assets/dfdd5460-edb2-4c0c-9484-c88ab91922f3" />
Query unknown keywords(LLM Need):
<img width="1435" height="516" alt="QQ_1769697575795" src="https://github.com/user-attachments/assets/3003aa3d-633a-4b97-bce1-60b183e8a33b" />

visualize_kg.py(It feels really messy... and when there are too many nodes, the edge labels aren't displayed anymore):
<img width="1551" height="999" alt="QQ_1769697684503" src="https://github.com/user-attachments/assets/65d6716e-c9b0-4f5a-9744-b7538dda2a62" />

memory_graph_builder.py:An interactive knowledge graph tool—nothing much to show right.


In short, the system is still very rough at this stage, but I personally feel it has a bit of potential. However, after building it all by myself up to now, I’m feeling extremely exhausted—both mentally and physically—and running low on inspiration. Maybe I need collaboration with others… though at the same time, there’s something really cool about slowly building a system entirely on my own.
