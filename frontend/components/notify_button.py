"""
Notify Button Component — Floating share button for WhatsApp group notifications.
Sends query activity summaries to the project group chat.
"""

import streamlit as st
from frontend.utils import api_post


def render_notify_button():
    """
    Render a shareable notify button in the top-right area.
    Shows a popup with query details and a WhatsApp share link.
    """

    # ── Floating Button CSS ───────────────────────────────
    st.markdown("""
    <style>
        .notify-container {
            position: fixed;
            top: 70px;
            right: 24px;
            z-index: 1000;
        }
        .notify-btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: linear-gradient(135deg, #25D366, #128C7E);
            color: white !important;
            border: none;
            border-radius: 50px;
            padding: 10px 20px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(37, 211, 102, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-decoration: none !important;
            font-family: 'Inter', sans-serif;
        }
        .notify-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 30px rgba(37, 211, 102, 0.55);
        }
        .notify-pulse {
            animation: notify-pulse-anim 2s ease-in-out infinite;
        }
        @keyframes notify-pulse-anim {
            0%, 100% { box-shadow: 0 4px 20px rgba(37, 211, 102, 0.4); }
            50% { box-shadow: 0 4px 30px rgba(37, 211, 102, 0.7); }
        }
    </style>
    """, unsafe_allow_html=True)

    # ── Check if there's a response to share ──────────────
    last_response = st.session_state.get("last_response")

    if last_response:
        # Show inline notification panel
        with st.sidebar:
            st.markdown("---")
            st.markdown("#### 📤 Share to Group")

            if st.button("📱 Share via WhatsApp", use_container_width=True, key="share_wa_btn"):
                # Generate WhatsApp notification link
                result = api_post("/api/notify", {
                    "query": last_response.get("query", ""),
                    "model": last_response.get("model_used", ""),
                    "answer_summary": str(last_response.get("answer", ""))[:300],
                    "response_type": "text",
                    "latency_ms": last_response.get("latency_ms", 0),
                    "intent": last_response.get("intent", ""),
                })

                if "error" not in result:
                    whatsapp_url = result.get("whatsapp_url", "")
                    group_link = result.get("group_link", "")

                    st.session_state["notify_result"] = result

                    # Create clickable link
                    st.markdown(f"""
                    <div style="background: rgba(37,211,102,0.1); border: 1px solid rgba(37,211,102,0.3);
                                border-radius: 12px; padding: 14px; margin-top: 8px;">
                        <div style="font-size: 0.8rem; color: #25D366; font-weight: 600; margin-bottom: 8px;">
                            ✅ Notification Ready!
                        </div>
                        <a href="{whatsapp_url}" target="_blank" class="notify-btn"
                           style="display: inline-flex; align-items: center; gap: 6px;
                                  background: linear-gradient(135deg, #25D366, #128C7E);
                                  color: white; text-decoration: none; padding: 8px 16px;
                                  border-radius: 8px; font-size: 0.8rem; font-weight: 600;">
                            📱 Send to WhatsApp
                        </a>
                        <div style="margin-top: 8px;">
                            <a href="{group_link}" target="_blank"
                               style="font-size: 0.75rem; color: #94a3b8; text-decoration: underline;">
                                Open Group Chat →
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error(f"❌ {result['error']}")

            # Show message preview
            if "notify_result" in st.session_state:
                with st.expander("📋 Message Preview", expanded=False):
                    st.code(st.session_state["notify_result"].get("message", ""), language="text")

    # ── Always show the floating button ───────────────────
    # This links directly to the WhatsApp group
    has_response = "true" if last_response else "false"

    st.markdown(f"""
    <div class="notify-container">
        <a href="https://chat.whatsapp.com/DIvuKQEblyWKVWm1uf7tlb" target="_blank"
           class="notify-btn {'notify-pulse' if last_response else ''}"
           title="Share to Project Group">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
            </svg>
            Share to Group
        </a>
    </div>
    """, unsafe_allow_html=True)
