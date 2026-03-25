# Terraform AI Generator (GCP)

This project uses a two-LLM system to generate and review Terraform code for Google Cloud.

## Features

- AI-generated Terraform infrastructure
- Builder + Reviewer workflow
- Custom naming prefix
- Custom CIDR configuration
- Custom section structure

## How to Run

```bash
python main.py

Requirements
Python 3
Ollama running locally
Installed models:
gpt-oss:120b-cloud (or similar)

Output

Generated files are saved in:

output_<prefix>/
