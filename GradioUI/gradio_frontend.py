import gradio as gr
from gradio_backend import Backend


class Frontend:
    def __init__(self, config):
        self.config = config
        self.backend = Backend()
        self.setup_ui()
        
        
    def launch(self):
        self.demo.launch(auth=("admin", "pass1234"),server_name="0.0.0.0")
        # self.demo.launch(server_name="0.0.0.0")

    def setup_ui(self):
        with gr.Blocks(title="Ascend Materials RAG") as self.demo:
            gr.Markdown("Ascend Materials GenAI Sales PoC")            

            with gr.Tab("Leads Directory"):
                dataframe_component = self.display_leads()
                # html_table = self.convert_to_html(dataframe_component)
                # gr.HTML(html_table)
                gr.DataFrame(dataframe_component, column_widths=["13%", "13%", "13%", "13%", "48%"], wrap=True, height=1000, datatype = ['str', 'markdown', 'str', 'str', 'str'])

            with gr.Tab("Chat"):

                with gr.Row():
                    with gr.Column(scale=4):
                        gr.Markdown("")
                    with gr.Column(scale=1):
                        token_slider = gr.Slider(minimum=1, maximum=10, step=1, value=5, label="Response Length")
                    
                with gr.Group():
                    response = gr.Textbox(show_label=False)
                    
                    with gr.Accordion("Sources", open=False):
                        # sources = gr.DataFrame(column_widths=["20%", "80%"], datatype=['markdown', 'str'], wrap=True)
                        sources = gr.HTML()


                with gr.Row(equal_height=True):
                    question = gr.Textbox(scale=3, label="Question", show_label=True, placeholder="Type your question here...")
                    submit_button = gr.Button("Submit", scale=1)
                if self.config == "KB":
                    submit_button.click(
                        self.chat_with_rag_kb,
                        inputs=[question, token_slider],
                        outputs=[response, sources]
                )  
                elif self.config == "AOSS":
                    submit_button.click(
                        self.chat_with_rag_aoss,
                        inputs=[question, token_slider],
                        outputs=[response, sources]
                )
                else:
                    raise ValueError("Incorrect Config: Must be 'AOSS' or 'KB'")
                
    def chat_with_rag_aoss(self, question, token_slider):
        answer, sources_df = self.backend.call_rag_aoss(question, token_slider)
        sources_df['FILE'] = sources_df['FILE'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

        return answer, sources_df.to_html(escape=False, index=False)
    
    def chat_with_rag_kb(self, question, token_slider):
        answer, sources_df = self.backend.call_rag_kb(question, token_slider)
        sources_df['FILE'] = sources_df['FILE'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

        return answer, sources_df.to_html(escape=False, index=False)
                
    def display_leads(self):
        df = self.backend.fetch_dataframe_from_s3()
        return df
    
    def convert_to_html(self, df):
                    df_html = df.copy()
                    df_html['URL'] = df_html['URL'].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')
                    return df_html.to_html(escape=False, index=False)
   
        

    
