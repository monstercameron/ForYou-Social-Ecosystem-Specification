# Network ASCII Architecture

## Purpose

Provide plain-text diagrams that represent the ForYou network, ranking flow, and user-owned attention model.

## Attention Ownership

```text
                 THE USER OWNS THE ALGORITHM FOR THEIR ATTENTION

   +-------------+        +-------------------+        +------------------+
   |  Protocol   | -----> | Candidate Content | -----> |  Ranking Engine  |
   | posts+index |        |  fetched by user  |        | local by default |
   +-------------+        +-------------------+        +---------+--------+
                                                                    |
                                                                    v
                                                         +------------------+
                                                         | Personal Feed    |
                                                         | user preferences |
                                                         | local context    |
                                                         +------------------+
```

## Network and Ranking Flow

```text
 +--------+     +--------+     +-------------+     +------------------+
 | Author | --> | Client | --> | Flow Nodes  | --> | Metadata Index   |
 +--------+     +--------+     +-------------+     +------------------+
      |               |                |                      |
      |               |                |                      |
      |               v                |                      v
      |        +--------------+        |              +------------------+
      |        | Verification | <------+              | Candidate Chunk  |
      |        | Nodes        |                       | Retrieval        |
      |        | BTC / ETH    |
      |        +------+-------+                       +---------+--------+
      |               |                                         |
      |               v                                         v
      |        +--------------+                         +------------------+
      |        | Payment Net  |                         | User Device      |
      |        | BTC / ETH    |                         | local prefs      |
      |        +--------------+                         | local model      |
      |                                                 +---------+--------+
      |                                                           |
      v                                                           v
 +-------------+                                          +------------------+
 | Full Content| <---------------------------------------- | Personal Feed    |
 | Storage     |                                           | ranked results   |
 +------+------+                                           +------------------+
        |
        v
 +-------------+
 | Retention   |
 | Layer       |
 +-------------+
```

## Resilience Model

```text
        MULTI-SOURCE RESILIENCE MODEL

 signed message
      +
 content address
      +
 many hosts
      +
 many caches
      +
 many discovery paths
      +
 verification after retrieval

 = no single required origin
```

## Availability Under Pressure

```text
       host A blocked
            X

client -> provider 1 -> miss
       -> provider 2 -> host C -> hit
       -> provider 3 -> host F -> hit

verify by content address
cache locally
keep reading
```

## Scaling by Temperature

```text
 HOT CONTENT
 - many caches
 - fast retrieval
 - wide replication

 WARM CONTENT
 - fewer copies
 - still recoverable from several hosts

 COLD CONTENT
 - retained more selectively
 - slower recovery acceptable
```

## Ranking Modes

```text
                     RANKING MODES

   1. Local
      candidates -> local model -> ranked feed

   2. Remote
      candidates -> hosted ranking service -> ranked feed

   3. Hybrid
      local prefs + candidates -> remote model -> ranked feed
```

## Low-Power Device Path

```text
 +------------------+      yes      +----------------------+
 | Device can run   | ----------->  | Use local ranking    |
 | useful local AI? |               | default path         |
 +--------+---------+               +----------------------+
          |
          | no
          v
 +------------------+               +----------------------+
 | Use smaller      | ----------->  | If still inadequate, |
 | local model      |               | use opt-in remote AI |
 +------------------+               +----------------------+
```
