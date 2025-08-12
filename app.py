import streamlit as st
import json
import asyncio
import aiohttp
import io

# Define the model to use for the API call
# This constant is a placeholder for the actual API model name, which will be provided by the runtime.
MODEL_NAME = "gemini-2.5-flash-preview-05-20"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent"

async def analyze_logs_with_llm(logs):
    """
    Asynchronously calls the Gemini API to analyze the provided logs.
    """
    # The API key is provided by the canvas environment.
    api_key = ""

    headers = {
        'Content-Type': 'application/json',
    }

    # Construct the prompt for the LLM
    prompt = f"""
    Analyze the following server logs and provide a summary of the root cause, potential next steps, and any recommended scripts or commands.
    The logs are as follows:

    {logs}

    Please format the response clearly with headings for "Root Cause", "Next Steps", and "Recommended Scripts/Commands".
    """

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "text/plain",
        }
    }

    # Implement exponential backoff for retries
    retries = 0
    while retries < 5:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{API_URL}?key={api_key}", headers=headers, json=payload) as response:
                    # Check for rate limiting or other transient errors
                    if response.status == 429 or response.status >= 500:
                        delay = 2 ** retries  # Exponential backoff
                        st.warning(f"API call failed with status {response.status}. Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                        retries += 1
                        continue

                    response.raise_for_status() # Raise an exception for bad status codes
                    result = await response.json()

                    if result.get("candidates"):
                        llm_response = result["candidates"][0]["content"]["parts"][0]["text"]
                        return llm_response
                    else:
                        st.error("Error: Could not get a valid response from the API.")
                        return "No analysis could be generated."

        except aiohttp.ClientError as e:
            st.error(f"Network or client error: {e}")
            return "An error occurred while connecting to the API."
        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON response: {e}")
            return "An error occurred while processing the API response."

    st.error("Max retries reached. Could not complete the API request.")
    return "Failed to get a response from the API after several retries."


def main():
    """
    Main function to create the Streamlit application UI.
    """
    st.set_page_config(page_title="LLM Log Analyzer", layout="wide")
    st.title("MANISH SINGH - LLM Log Analyzer")
    st.markdown("Paste your logs below or upload a file. The LLM will analyze them to provide a root cause summary and next steps.")

    # File uploader widget
    uploaded_file = st.file_uploader("Upload a log file", type=["log", "txt"])
    
    logs_input = ""
    if uploaded_file is not None:
        # Read the file content as a string
        string_io = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        logs_input = string_io.read()
    else:
        # Text area for user to input logs if no file is uploaded
        logs_input = st.text_area("Or paste logs here:", height=300, placeholder="e.g., NGINX logs, system logs, etc.")

    # Button to trigger the analysis
    if st.button("Analyze Logs", use_container_width=True):
        if logs_input:
            with st.spinner("Analyzing logs... Please wait."):
                # Use asyncio to run the async function
                llm_analysis = asyncio.run(analyze_logs_with_llm(logs_input))
                
                # Store the analysis in session state
                st.session_state["llm_analysis_result"] = llm_analysis
                
                # Display the results
                st.subheader("Analysis Results")
                st.markdown(llm_analysis)
        else:
            st.warning("Please paste some logs or upload a file to analyze.")

    # Add a download button if an analysis result exists in the session state
    if "llm_analysis_result" in st.session_state and st.session_state["llm_analysis_result"]:
        st.download_button(
            label="Download Analysis",
            data=st.session_state["llm_analysis_result"],
            file_name="llm_log_analysis.txt",
            mime="text/plain",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
