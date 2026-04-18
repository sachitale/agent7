# Analyzer — Sequence Flow

## analyze command

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontFamily": "'Source Code Pro', Menlo, 'Courier New', monospace"}}}%%
sequenceDiagram
    actor User
    participant CLI
    participant Graph as LangGraph
    participant Extract as extract node
    participant Retrieve as retrieve node
    participant Reason as reason node
    participant Refine as refine node
    participant Embedder
    participant Store as VectorStore
    participant ChromaDB
    participant LLM as LLM<br/>(Claude / OpenAI / Ollama)
    participant Output as output.jsonl

    User->>CLI: analyzer analyze<br/>--events events.jsonl<br/>--db ./chroma<br/>--llm-provider claude

    CLI->>CLI: build LLM (get_llm)<br/>build Embedder (get_embedder)<br/>open VectorStore

    CLI->>Graph: build_graph(llm, embedder, store)
    Graph-->>CLI: compiled graph

    loop for each FailureEvent
        CLI->>Graph: invoke(initial_state)

        Graph->>Extract: extract_node(state)
        Extract->>Extract: detect language from stack trace<br/>build initial search queries
        Extract-->>Graph: state + language_hint + search_queries

        Graph->>Retrieve: retrieve_node(state)
        Retrieve->>Embedder: embed(queries)
        Embedder-->>Retrieve: query vectors
        Retrieve->>Store: query(vector, top_k)
        Store->>ChromaDB: query embeddings
        ChromaDB-->>Store: ids, documents, metadatas, distances
        Store-->>Retrieve: hits
        Retrieve-->>Graph: state + retrieved_chunks

        Graph->>Reason: reason_node(state)
        Reason->>Reason: format chunks + failure into prompt
        Reason->>LLM: invoke([SystemMessage, HumanMessage])
        LLM-->>Reason: JSON response<br/>(hypothesis, confidence,<br/>needs_more_context, refined_queries)
        Reason-->>Graph: state + hypothesis + confidence + iterations+1

        alt needs_more_context AND iterations < max_iterations
            Graph->>Refine: refine_node(state)
            Refine-->>Graph: state + updated search_queries
            Graph->>Retrieve: retrieve_node(state)
            note over Retrieve,LLM: loop repeats
        else confident OR max iterations reached
            Graph-->>CLI: final state
        end

        CLI->>Output: write_jsonl(final_state)
        CLI-->>User: print_report (hypothesis, explanation,<br/>confidence, relevant_files)
    end

    CLI-->>User: Done — reports written to analysis.jsonl
```

## LangGraph node structure

```mermaid
%%{init: {"theme": "default", "themeVariables": {"fontFamily": "'Source Code Pro', Menlo, 'Courier New', monospace"}}}%%
sequenceDiagram
    participant START
    participant extract
    participant retrieve
    participant reason
    participant refine
    participant END

    START->>extract: FailureEvent fields
    extract->>retrieve: + language_hint, search_queries
    retrieve->>reason: + retrieved_chunks
    reason->>reason: LLM call

    alt needs_more_context AND iterations < max
        reason->>refine: + _refined_queries
        refine->>retrieve: + updated search_queries
    else done
        reason->>END: final state
    end
```
