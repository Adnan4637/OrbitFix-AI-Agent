orbit-root-cause-agent/
│
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
├── .env.example
│
├── docs/
│   ├── problem-statement.md
│   ├── architecture.md
│   ├── use-cases.md
│   ├── demo-script.md
│   └── api-flow.md
│
├── backend/
│   │
│   ├── main.py
│   ├── config.py
│   │
│   ├── api/
│   │   ├── webhook.py
│   │   └── health.py
│   │
│   ├── services/
│   │   ├── gitlab_client.py
│   │   ├── orbit_client.py
│   │   ├── log_collector.py
│   │   ├── commit_collector.py
│   │   ├── mr_collector.py
│   │   ├── root_cause_engine.py
│   │   ├── impact_analyzer.py
│   │   ├── report_generator.py
│   │   ├── llm_service.py
│   │   └── comment_publisher.py
│   │
│   ├── models/
│   │   ├── pipeline.py
│   │   ├── report.py
│   │   ├── commit.py
│   │   ├── merge_request.py
│   │   └── impact.py
│   │
│   ├── prompts/
│   │   ├── root_cause_prompt.txt
│   │   └── impact_prompt.txt
│   │
│   └── utils/
│       ├── logger.py
│       ├── parser.py
│       └── helpers.py
│
├── sample-data/
│   │
│   ├── logs/
│   │   ├── import_error.log
│   │   ├── dependency_error.log
│   │   ├── test_failure.log
│   │   └── yaml_failure.log
│   │
│   ├── reports/
│   │   └── sample_report.md
│   │
│   └── orbit/
│       └── sample_graph.json
│
├── tests/
│   ├── test_gitlab_client.py
│   ├── test_orbit_client.py
│   ├── test_root_cause_engine.py
│   ├── test_impact_analyzer.py
│   └── test_report_generator.py
│
├── scripts/
│   ├── setup.sh
│   ├── run_local.sh
│   ├── trigger_webhook.py
│   └── create_demo_failure.py
│
└── .gitlab/
    └── demo-project/
        ├── .gitlab-ci.yml
        ├── app.py
        ├── requirements.txt
        └── tests/