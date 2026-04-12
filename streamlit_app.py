imort streamlit as st
import pandas as pd
import numpy as np
import datetime as dt

st.set_page_config(layout="wide")

# -------------------------
# HEADER
# -------------------------
st.title("PetroStratum — War Room")
st.caption("Synchronization | Energy | Flows | Risk")

# -------------------------
# TABS
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Live",
        "Scenarios",
            "Negotiation",
                "Historical"
                ])

                # -------------------------
                # LIVE
                # -------------------------
                with tab1:
                    st.subheader("Live System State")

                        col1, col2, col3, col4 = st.columns(4)

                            col1.metric("Brent (proxy)", "113", "+1.2")
                                col2.metric("Freight Pressure", "High", "↑")
                                    col3.metric("Volatility (MOVE proxy)", "Elevated", "↑")
                                        col4.metric("Synchronization Gap", "Widening", "⚠️")

                                            st.markdown("### System Interpretation")

                                                st.warning(
                                                        "Markets are pricing execution. "
                                                                "Physical systems are not synchronized. "
                                                                        "Gap between financial time and physical time is expanding."
                                                                            )

                                                                            # -------------------------
                                                                            # SCENARIOS
                                                                            # -------------------------
                                                                            with tab2:
                                                                                st.subheader("Scenario Engine")

                                                                                    scenario = st.selectbox(
                                                                                            "Select scenario",
                                                                                                    ["Base Case", "Escalation", "De-escalation"]
                                                                                                        )

                                                                                                            if scenario == "Base Case":
                                                                                                                    st.info("Slow coordination. Persistent friction.")
                                                                                                                        elif scenario == "Escalation":
                                                                                                                                st.error("Transmission phase. Energy binds system.")
                                                                                                                                    else:
                                                                                                                                            st.success("Temporary absorption. Fragility remains latent.")

                                                                                                                                            # -------------------------
                                                                                                                                            # NEGOTIATION
                                                                                                                                            # -------------------------
                                                                                                                                            with tab3:
                                                                                                                                                st.subheader("Negotiation Dynamics")

                                                                                                                                                    st.markdown("""
                                                                                                                                                        Execution is not a statement.  
                                                                                                                                                            It is a coordination function across layers.
                                                                                                                                                                """)

                                                                                                                                                                    st.markdown("**Key constraint:**")
                                                                                                                                                                        st.write("Time mismatch between diplomacy and logistics")

                                                                                                                                                                        # -------------------------
                                                                                                                                                                        # HISTORICAL
                                                                                                                                                                        # -------------------------
                                                                                                                                                                        with tab4:
                                                                                                                                                                            st.subheader("Historical Analogues")

                                                                                                                                                                                data = pd.DataFrame({
                                                                                                                                                                                        "Year": [2008, 2014, 2020, 2022, 2026],
                                                                                                                                                                                                "Shock": ["GFC", "Oil collapse", "COVID", "Ukraine", "Hormuz risk"]
                                                                                                                                                                                                    })

                                                                                                                                                                                                        st.table(data)
