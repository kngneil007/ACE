import json
import urllib.request
import urllib.error
import os

OLLAMA_URL = "http://localhost:11434/api/generate"

# Make sure this model exists in: ollama list
BUILDER_MODEL = "you can't use mine, sorry"# <---- use ollama list to find yours
REVIEWER_MODEL = "you cant use mine sorry" # <---- or download ollama


# -------------------------------
# USER INPUT
# -------------------------------
def get_user_input():
    print("\n=== User Configuration ===")

    project_id = input("Enter your GCP Project ID: ")
    region = input("Enter default region (e.g. us-central1): ")
    prefix = input("Enter a naming prefix (e.g. demo): ")

    return project_id, region, prefix


# -------------------------------
# CIDR INPUT
# -------------------------------
def get_cidr():
    print("\n=== CIDR Configuration ===")

    num = input("Enter a number (1-99) for CIDR (10.X.0.0/16): ")

    try:
        num = int(num)
        if 1 <= num <= 99:
            return f"10.{num}.0.0/16"
    except:
        pass

    print("Invalid input. Using default 10.0.0.0/16")
    return "10.0.0.0/16"


# -------------------------------
# SECTION NAMING
# -------------------------------
def get_section_names():
    print("\n=== Section Naming ===")

    vpc = input("Name for VPC section (default: VPC): ") or "VPC"
    network = input("Name for Network section (default: Network): ") or "Network"
    subnets = input("Name for Subnets section (default: Subnets): ") or "Subnets"
    firewall = input("Name for Firewall section (default: Firewall): ") or "Firewall"
    compute = input("Name for Compute section (default: Compute): ") or "Compute"

    return vpc, network, subnets, firewall, compute


# -------------------------------
# OLLAMA CALL
# -------------------------------
def call_ollama(model: str, prompt: str) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=1200) as response:
            body = response.read().decode("utf-8")
            parsed = json.loads(body)
            return parsed.get("response", "").strip()
    except urllib.error.URLError as e:
        return f"[ERROR] Could not reach Ollama: {e}"
    except Exception as e:
        return f"[ERROR] Unexpected error: {e}"


# -------------------------------
# BUILDER PROMPT
# -------------------------------
def build_builder_prompt(project_id, region, prefix, cidr_block, sections) -> str:
    vpc, network, subnets, firewall, compute = sections

    return f"""
You are a Terraform Builder.

Generate Terraform code for Google Cloud with:

- project_id: {project_id}
- region: {region}
- naming prefix: {prefix}
- CIDR base: {cidr_block}

Create:

- 1 VPC network
- 2 subnets inside the CIDR range
- firewall rules for HTTP (80) and SSH (22)
- 1 VM instance

Structure code into sections:
# --- {vpc} ---
# --- {network} ---
# --- {subnets} ---
# --- {firewall} ---
# --- {compute} ---

Requirements:
- Use Google provider
- Use prefix "{prefix}" in ALL resource names
- Use CIDR range {cidr_block}
- Do NOT use AWS
- Output Terraform code only
""".strip()


# -------------------------------
# REVIEWER PROMPT (FIXED)
# -------------------------------
def build_reviewer_prompt(terraform_code: str) -> str:
    return f"""
You are a strict Terraform Reviewer.

Review the Terraform code below.

Return your review EXACTLY in this format:

REVIEW_SUMMARY:
<summary>

STRENGTHS:
- item

ISSUES_FOUND:
- item

RECOMMENDED_FIXES:
- item

IMPROVED_TERRAFORM:
```hcl
# improved terraform code here
{terraform_code}
""".strip()
# -------------------------------
#EXTRACT IMPROVED CODE
# -------------------------------

def extract_improved_terraform(review_text: str) -> str:
    marker = "IMPROVED_TERRAFORM:"
    marker_index = review_text.find(marker)
    
    if marker_index == -1:
      return ""

    code_start = review_text.find("```hcl", marker_index)
    if code_start == -1:
        return ""

    code_start += len("```hcl")
    code_end = review_text.find("```", code_start)
    if code_end == -1:
        return ""

    return review_text[code_start:code_end].strip()

# -------------------------------
#SAVE FILES
#-------------------------------

def save_project_files(prefix, filename, content):
    folder = f"output_{prefix}"
    os.makedirs(folder, exist_ok=True)
    
    with open(f"{folder}/{filename}", "w", encoding="utf-8") as f:
        f.write(content)
        
#-------------------------------
#MAIN
#-------------------------------

def main():
    print("\n=== Two-LLM Terraform Demo (ACE VERSION) ===\n")
    
    # User inputs
    project_id, region, prefix = get_user_input()
    sections = get_section_names()
    cidr_block = get_cidr()

    # Builder
    print("\n>>> Builder is generating Terraform code...")
    builder_prompt = build_builder_prompt(
        project_id,
        region,
        prefix,
        cidr_block,
        sections
    )

    terraform_code = call_ollama(BUILDER_MODEL, builder_prompt)

    print("\n--- Generated Terraform Code ---\n")
    print(terraform_code)

    save_project_files(prefix, "generated.tf", terraform_code)

    # Reviewer
    print("\n>>> Reviewer is reviewing the generated code...")
    reviewer_prompt = build_reviewer_prompt(terraform_code)
    review = call_ollama(REVIEWER_MODEL, reviewer_prompt)

    print("\n--- Review Output ---\n")
    print(review)

    save_project_files(prefix, "review.txt", review)

    # Extract improved Terraform
    improved_terraform = extract_improved_terraform(review)

    if improved_terraform:
        print("\n--- Improved Terraform Code ---\n")
        print(improved_terraform)
        save_project_files(prefix, "improved.tf", improved_terraform)
    else:
        print("\n[INFO] No improved Terraform code found in the review.")
        
        
if __name__ == "__main__":
    main()