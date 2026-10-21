---
name: rl-paper-tutoring
description: "Explain a specific RL or VLA paper passage, equation, or data flow to a learner who reads the source and asks focused questions."
license: MIT
---

# RL and VLA paper tutoring

Begin at the passage, figure, or formula the learner identified. If the location
is unknown and materially changes the answer, ask for it. Do not replace a focused
question with a full literature review.

1. Explain the immediate idea in plain language, retaining English technical
   terms when useful for reading the source.
2. Define symbols and module inputs/outputs before using them. For a pipeline,
   draw the data flow in text, such as observation → representation → policy →
   action chunk. Mark which components are trained or frozen based on the paper.
3. Use one small robot task or numerical example to connect the explanation to
   the source. Clearly label invented example numbers.
4. Separate nearby concepts when they cause confusion: advantage versus value;
   collection-time versus current-policy probability; internal VLM tokens versus
   a separately added token module; online/offline versus on-/off-policy.
5. If the abstract depends on later method details, give the minimum useful
   intuition and return to those details when needed. Offer a short understanding
   check when it helps; do not infer mastery from silence.

Read the actual source for claims about a particular method. When it is unavailable,
explain the general concept and state which paper-specific details remain open.
Do not turn a learning discussion into an unrequested experiment or deployment.
