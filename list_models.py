import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure API
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

output = []
output.append("Available Gemini Models that support generateContent:")
output.append("=" * 80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        output.append(f"\nModel Name: {model.name}")
        output.append(f"Display Name: {model.display_name}")
        output.append("-" * 80)

# Print to console
for line in output:
    print(line)

# Save to file
with open('available_models.txt', 'w') as f:
    f.write('\n'.join(output))

print("\n\nOutput saved to available_models.txt")
