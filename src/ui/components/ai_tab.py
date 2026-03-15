"""
AI tab component for asking questions about running data.
"""

import streamlit as st
from ...analysis import ClaudeClient


class AITabComponent:
    """Claude AI integration tab."""

    EXAMPLE_QUESTIONS = [
        "What day of the week do I run the most?",
        "How has my average heart rate changed over time?",
        "What's my longest run distance and when did I run it?",
        "Based on my data, what training recommendations would you give?",
        "Compare my running performance in December vs January",
        "What's my typical run distance and should I push longer?",
    ]

    @staticmethod
    def render(data_context: str) -> None:
        """
        Render the AI tab.

        Args:
            data_context: Context string with running data
        """
        st.subheader("💬 Ask AI About Your Running")

        st.markdown("""
        Ask questions about your running performance, training insights, or get personalized advice.
        The AI assistant has access to your entire running data context.
        """)

        client = ClaudeClient()

        if not client.is_configured():
            st.warning(
                "⚠️ Perplexity API key not configured. "
                "Please add `PERPLEXITY_API_KEY` to your `.env` file."
            )
            return
        
        # Question input
        question = st.text_area(
            "Ask a question about your running:",
            placeholder=(
                "e.g., What's my average pace on Thursdays? "
                "Should I increase my long run distance? "
                "What's my training trend?"
            ),
            height=100
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            ask_button = st.button("🤔 Ask", use_container_width=True)
        
        if ask_button and question:
            with st.spinner("🤖 Thinking..."):
                response = client.query(question, data_context)
            
            st.markdown("### Response")
            st.markdown(response)
            
            # Add helpful context info
            with st.expander("📊 Data Used for This Analysis"):
                st.markdown(data_context)
        
        elif ask_button and not question:
            st.warning("Please enter a question first!")
        
        # Example questions
        st.divider()
        st.markdown("### Example Questions")
        
        for i, example in enumerate(AITabComponent.EXAMPLE_QUESTIONS):
            if st.button(f"💡 {example}", key=f"example_{i}"):
                with st.spinner("🤖 Thinking..."):
                    response = client.query(example, data_context)
                
                st.markdown("### Response")
                st.markdown(response)
