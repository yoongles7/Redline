# Redline

## What it is
A pre-deployment blast radius analyzer for AI agents.

## Input
A JSON config with:
- agent_name (string)
- intended_purpose (string, one sentence describing what the agent is supposed to do)
- tools (list), each with:
  - name (string)
  - description (string)
  - parameters (list of strings)
  - permissions (list, from: read, write, execute, network)

## Process
1. Parse the agent config
2. Classify each tool by permission dimension
3. Detect attack paths (chains of tools that enable unintended actions)
4. Score each path against intended purpose:
   - Expected for purpose -> lower severity
   - Unexpected for purpose -> higher severity
5. Compute overall blast radius score (low / medium / high / critical)

## Detection rules
| Combination | Risk category | Severity |
|---|---|---|
| read + network | Data exfiltration | HIGH |
| execute alone | Arbitrary code execution | CRITICAL|
| execute + write | Persistence | HIGH|
| execute + network | Command & control | CRITICAL |
| read + write + network | Full compromise | CRITICAL |
| write alone | Data tampering | MEDIUM | 
| read + write | Data modification | MEDIUM |

## Scoring
- Overall blast radius = highest severity among detected paths
- if no paths detected -> LOW
- Severity order: LOW < MEDIUM < HIGH < CRITICAL

## Output
A structured report:
- agent_name
- overall blast radius score
- list of attack paths, each with:
  - chain (list of tool names)
  - category
  - severity
  - explanation
- list of mitigations, each with:
  - action ("remove" or "restrict")
  - tool
  - reason
  - alternative (if restrict: JIT, scoping, approval threshold, segmentation)

## Scope disclaimer
Redline covers tool permission blast radius.
It does NOT cover runtime behaviour, memory poisoning, goal manipulation, or multi-agent risks.

## Sample data
Sample inputs are reconstructed from public incident reporting.
Sources listed in README.md.