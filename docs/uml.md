# Module Responsibilities

This diagram shows module-level responsibilities after the refactor. It is intentionally simple and focuses on boundaries rather than implementation details.

```mermaid
classDiagram
    class Config {
        <<module>>
        SERVER_NAME
        DEFAULT_MAX_GENERATE
        DEFAULT_TEMPERATURE
        DEFAULT_TOP_K
        DEFAULT_SENSOR_SIZE
        DEFAULT_SEED
        ALLOWED_DETAIL_LEVELS
    }

    class Server {
        <<module>>
        creates FastMCP app
        registers tools
        registers resources
        main()
    }

    class MCPTools {
        <<module>>
        get_server_capabilities()
        list_clients()
        get_sample_history()
        get_prediction_input_sample()
        predict_next_basket()
        recommend_next_action()
        get_account_reorder_brief()
    }

    class MCPResources {
        <<module>>
        model_card()
        register_resources()
    }

    class Predictor {
        <<module>>
        OrderPredictor
        smart_inference_onnx()
        loads local dataset
        loads local ONNX model
    }

    class TokenUtils {
        <<module>>
        split_tokens()
        readable_items_from_tokens()
        extract_time_prediction()
        compact_token_preview()
    }

    class SalesBrief {
        <<module>>
        make_sales_recommendation()
        talking points helper
    }

    class Evidence {
        <<module>>
        reason codes
        evidence summary
        model signals
        limitations
    }

    class Safety {
        <<module>>
        recommendation-only boundary
    }

    Server --> Config
    Server --> MCPTools
    Server --> MCPResources
    MCPTools --> Config
    MCPTools --> Predictor
    MCPTools --> TokenUtils
    MCPTools --> SalesBrief
    MCPTools --> Evidence
    MCPTools --> Safety
```

## Boundary Notes

- `server.py` owns app setup, not prediction or business logic.
- `mcp/tools.py` owns MCP tool behavior and lazy predictor loading.
- `backend/predictor.py` owns model and dataset access.
- `business/` owns sales wording, evidence summaries, and safety boundaries.
- `utils/token_utils.py` owns token parsing and readable conversion.
- `data/` and `vendor/` remain local-only and are not public source modules.

