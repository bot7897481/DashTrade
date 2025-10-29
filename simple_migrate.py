"""
Streamlit app to run database migration
Run this via: streamlit run simple_migrate.py
"""
import streamlit as st
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Database Migration", page_icon="🔧")

st.title("🔧 DashTrade Database Migration")
st.markdown("---")

# Check DATABASE_URL
if not os.getenv('DATABASE_URL'):
    st.error("❌ DATABASE_URL environment variable not set!")
    st.info("Please set DATABASE_URL in your Replit Secrets.")
    st.stop()

st.success("✅ DATABASE_URL is set")

st.markdown("""
### This migration will:
1. ✅ Create `users` table with role support (user, admin, superadmin)
2. ✅ Add `user_id` to watchlist, alerts, and user_preferences tables
3. ✅ Add proper constraints and indexes
4. ✅ Preserve all existing data

### After migration:
- You'll need to create a superadmin account using `create_admin.py`
- Then restart the app and login with authentication
""")

st.markdown("---")

if st.button("🚀 Run Migration Now", type="primary"):
    with st.spinner("Running migration..."):
        try:
            from migrate_database import run_migration
            
            # Capture output
            import io
            from contextlib import redirect_stdout
            
            output_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer):
                run_migration()
            
            output = output_buffer.getvalue()
            
            st.success("✅ Migration completed successfully!")
            
            with st.expander("Migration Details"):
                st.code(output)
            
            st.markdown("---")
            st.markdown("### Next Steps:")
            st.info("""
1. Stop this migration app
2. Run in Shell: `python create_admin.py`  
3. Create your superadmin account
4. Restart the main app
5. Login and enjoy! 🎉
            """)
            
        except Exception as e:
            st.error(f"❌ Migration failed: {str(e)}")
            st.exception(e)

st.markdown("---")
st.caption("DashTrade v1.0 - Authentication Setup")
