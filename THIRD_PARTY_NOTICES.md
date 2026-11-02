# Attribution and third-party notices

The receiver is reused from Ibrahim Arshad’s local AI-assisted Deep Agents experiment, not an upstream SDK contribution. The runtime used in historical experiments is provided by Deep Agents, LangChain, and LangGraph. No runtime implementation is included in this extraction.

The following upstream MIT notice is retained for attribution and any applicable reused material; it does not assert that the local experimental receiver was authored by LangChain.

MIT License

Copyright (c) LangChain, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Local experimental middleware and recorder

The conservative middleware module and Recorder class are reused from Ibrahim Arshad's local AI-assisted Deep Agents experiment. Their source/destination identities and extraction changes are recorded in `results/manifest.json`. The conservative module is byte-identical; the Recorder class source is unchanged within a standalone module. No upstream Deep Agents, LangChain or LangGraph framework implementation is copied here; those projects are runtime dependencies for the opt-in scripted fixture. The MIT notice above remains retained.
