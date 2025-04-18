from typing import Any, Dict, List, Optional


import pandas as pd
import requests
import snowflake.connector
import streamlit as st
import speech_recognition as sr
import pyttsx3
from speech_recognition.recognizers import google
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from audio_recorder_streamlit import audio_recorder
from google.cloud import speech_v1 as speech




HOST = "ZVFIDAY-LLB69903.snowflakecomputing.com"
DATABASE = "CORTEX_SEARCH_TUTORIAL_DB"
SCHEMA = "PUBLIC"
STAGE = "BEVERAGE_DATA_STAGE"
FILE = "beverage_order_model.yaml"

if 'CONN' not in st.session_state or st.session_state.CONN is None:
    st.session_state.CONN = snowflake.connector.connect(
        user="DKUMARJAYAKUMAR",
        password="Vivega@11223344",
        account="LLB69903",
        host=HOST,
        port=443,
        warehouse="SEARCH_WH",
        role="ACCOUNTADMIN",
    )


def send_message(prompt: str) -> Dict[str, Any]:
    """Calls the REST API and returns the response."""
    request_body = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
        "semantic_model_file": f"@{DATABASE}.{SCHEMA}.{STAGE}/{FILE}",
    }
    resp = requests.post(
        url=f"https://{HOST}/api/v2/cortex/analyst/message",
        json=request_body,
        headers={
            "Authorization": f'Snowflake Token="{st.session_state.CONN.rest.token}"',
            "Content-Type": "application/json",
        },
    )
    request_id = resp.headers.get("X-Snowflake-Request-Id")
    if resp.status_code < 400:
        return {**resp.json(), "request_id": request_id}  # type: ignore[arg-type]
    else:
        raise Exception(
            f"Failed request (id: {request_id}) with status {resp.status_code}: {resp.text}"
        )


def process_message(prompt: str) -> None:
    """Processes a message and adds the response to the chat."""
    st.session_state.messages.append(
        {"role": "user", "content": [{"type": "text", "text": prompt}]}
    )
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            response = send_message(prompt=prompt)
            request_id = response["request_id"]
            content = response["message"]["content"]
            display_content(content=content, request_id=request_id)  # type: ignore[arg-type]
    st.session_state.messages.append(
        {"role": "assistant", "content": content, "request_id": request_id}
    )


def display_content(
    content: List[Dict[str, str]],
    request_id: Optional[str] = None,
    message_index: Optional[int] = None,
) -> None:
    """Displays a content item for a message."""
    stt_button = Button(label="Speak", width=100)
    message_index = message_index or len(st.session_state.messages)
    # if request_id:
    #     with st.expander("Request ID", expanded=False):
    #         st.markdown(request_id)
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            with st.expander("Suggestions", expanded=True):
                for suggestion_index, suggestion in enumerate(item["suggestions"]):
                    if st.button(suggestion, key=f"{message_index}_{suggestion_index}"):
                        st.session_state.active_suggestion = suggestion
        elif item["type"] == "sql":
            with st.expander("SQL Query", expanded=False):
                st.code(item["statement"], language="sql")
            with st.expander("Results", expanded=True):
                with st.spinner("Running SQL..."):
                    df = pd.read_sql(item["statement"], st.session_state.CONN)
                    if len(df.index) > 1:
                        data_tab, line_tab, bar_tab, area_tab = st.tabs(
                            ["Data", "Line Chart", "Bar Chart", "Area Chart"]
                        )
                        data_tab.dataframe(df)
                        if len(df.columns) > 1:
                            df = df.set_index(df.columns[0])
                        with line_tab:
                            st.line_chart(df)
                        with bar_tab:
                            st.bar_chart(df)
                        with area_tab:
                            st.area_chart(df)
                    else:
                        st.dataframe(df)


st.title(":cup_with_straw: ORDE AI 🔍")
#initialize the recognizer
r = sr.Recognizer()
# audio_value = st.audio_input("Record a voice message")
#client = speech.SpeechAsyncClient()
audio_bytes = audio_recorder(recording_color="#6aa36f", neutral_color="#e82c58")
if audio_bytes:
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    #sample_rate_hertz=44100,
                    language_code="en-US",
                    model="default",
                    audio_channel_count=2,
                    enable_word_confidence=True,
                    enable_word_time_offsets=True,
    )
    
    #operation = speech.SpeechClient().long_running_recognize(config=config, audio=audio)
    #conversion = operation.result(timeout=90)
    #for result in conversion.results:
    #    pass
                  
    #reccord_text = (result.alternatives[0].transcript)


# st.markdown(f"Semantic Model: `{FILE}`")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.suggestions = []
    st.session_state.active_suggestion = None

for message_index, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        display_content(
            content=message["content"],
            request_id=message.get("request_id"),
            message_index=message_index,
        )




def record_text():
    # Loop in case of error
    while(1):
        try:
            st.audio(audio_value)
            audiodata = r.record(audio_value)

            Mytext = r.recognize_google(audiodata)
            
            return Mytext

        except sr.RequestError as e:
            print("could not request result: {0}".format(e))

        except sr.UnknownValueError:
            print("unknown value")

    return
    



       
        
if user_input := st.chat_input("What is your question?"):
    #record_text()
    process_message(prompt=reccord_text)

if st.session_state.active_suggestion:
    process_message(prompt=st.session_state.active_suggestion)
    st.session_state.active_suggestion = None
