import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configure Streamlit page
st.set_page_config(
    page_title="E-commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1rem;
    border-radius: 10px;
    color: white;
    margin: 0.5rem 0;
}
.platform-header {
    font-size: 1.5rem;
    font-weight: bold;
    color: #333;
    margin: 1rem 0;
    padding: 0.5rem;
    background-color: #f0f2f6;
    border-radius: 5px;
}
.warning-box {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    border-radius: 5px;
    padding: 1rem;
    margin: 1rem 0;
}
.success-box {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    border-radius: 5px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

class EcommerceAnalyzer:
    def __init__(self):
        self.meesho_sales = None
        self.meesho_returns = None
        self.flipkart_data = None
        self.amazon_data = None
        
    def load_meesho_data(self, sales_file, returns_file=None):
        """Load and process Meesho sales and returns data"""
        try:
            # Load sales data
            self.meesho_sales = pd.read_csv(sales_file)
            
            # Clean column names
            self.meesho_sales.columns = self.meesho_sales.columns.str.strip()
            
            # Convert date columns
            if 'order_date' in self.meesho_sales.columns:
                self.meesho_sales['order_date'] = pd.to_datetime(self.meesho_sales['order_date'], errors='coerce')
            
            # Process returns data if provided
            if returns_file is not None:
                try:
                    self.meesho_returns = pd.read_csv(returns_file)
                    self.meesho_returns.columns = self.meesho_returns.columns.str.strip()
                except:
                    st.warning("Could not process returns file. It might be in a different format.")
                    
            return True
        except Exception as e:
            st.error(f"Error loading Meesho data: {str(e)}")
            return False
    
    def load_flipkart_data(self, file):
        """Load and process Flipkart data"""
        try:
            self.flipkart_data = pd.read_csv(file)
            self.flipkart_data.columns = self.flipkart_data.columns.str.strip()
            return True
        except Exception as e:
            st.error(f"Error loading Flipkart data: {str(e)}")
            return False
    
    def load_amazon_data(self, file):
        """Load and process Amazon data"""
        try:
            self.amazon_data = pd.read_csv(file)
            self.amazon_data.columns = self.amazon_data.columns.str.strip()
            
            # Convert date columns
            date_columns = ['Invoice Date', 'Order Date', 'Shipment Date']
            for col in date_columns:
                if col in self.amazon_data.columns:
                    self.amazon_data[col] = pd.to_datetime(self.amazon_data[col], errors='coerce')
                    
            return True
        except Exception as e:
            st.error(f"Error loading Amazon data: {str(e)}")
            return False
    
    def analyze_meesho_data(self):
        """Analyze Meesho sales data"""
        if self.meesho_sales is None:
            return None
            
        analysis = {}
        
        # Basic metrics
        analysis['total_orders'] = len(self.meesho_sales)
        analysis['total_sales'] = self.meesho_sales['total_invoice_value'].sum()
        analysis['total_tax'] = self.meesho_sales['tax_amount'].sum()
        analysis['taxable_sales'] = self.meesho_sales['total_taxable_sale_value'].sum()
        
        # State-wise analysis
        analysis['state_wise'] = self.meesho_sales.groupby('end_customer_state_new').agg({
            'total_invoice_value': 'sum',
            'tax_amount': 'sum',
            'quantity': 'sum'
        }).round(2)
        
        # Monthly analysis
        if 'order_date' in self.meesho_sales.columns:
            self.meesho_sales['month'] = self.meesho_sales['order_date'].dt.to_period('M')
            analysis['monthly'] = self.meesho_sales.groupby('month').agg({
                'total_invoice_value': 'sum',
                'tax_amount': 'sum',
                'quantity': 'sum'
            }).round(2)
        
        # Product analysis
        analysis['product_performance'] = self.meesho_sales.groupby('hsn_code').agg({
            'total_invoice_value': 'sum',
            'tax_amount': 'sum',
            'quantity': 'sum'
        }).round(2)
        
        # Tax rate analysis
        analysis['tax_rate_analysis'] = self.meesho_sales.groupby('gst_rate').agg({
            'total_invoice_value': 'sum',
            'tax_amount': 'sum',
            'quantity': 'sum'
        }).round(2)
        
        return analysis
    
    def analyze_amazon_data(self):
        """Analyze Amazon sales data"""
        if self.amazon_data is None:
            return None
            
        analysis = {}
        
        # Filter for actual transactions (not cancellations)
        shipments = self.amazon_data[self.amazon_data['Transaction Type'] == 'Shipment']
        refunds = self.amazon_data[self.amazon_data['Transaction Type'] == 'Refund']
        cancellations = self.amazon_data[self.amazon_data['Transaction Type'] == 'Cancel']
        
        # Basic metrics
        analysis['total_shipments'] = len(shipments)
        analysis['total_refunds'] = len(refunds)
        analysis['total_cancellations'] = len(cancellations)
        
        if not shipments.empty:
            analysis['total_sales'] = shipments['Invoice Amount'].sum()
            analysis['total_tax'] = shipments['Total Tax Amount'].sum()
            analysis['tax_exclusive_gross'] = shipments['Tax Exclusive Gross'].sum()
            
            # State-wise analysis
            analysis['state_wise'] = shipments.groupby('Ship To State').agg({
                'Invoice Amount': 'sum',
                'Total Tax Amount': 'sum',
                'Quantity': 'sum'
            }).round(2)
            
            # Monthly analysis
            if 'Order Date' in shipments.columns:
                shipments['month'] = shipments['Order Date'].dt.to_period('M')
                analysis['monthly'] = shipments.groupby('month').agg({
                    'Invoice Amount': 'sum',
                    'Total Tax Amount': 'sum',
                    'Quantity': 'sum'
                }).round(2)
            
            # Product analysis
            analysis['product_performance'] = shipments.groupby('Hsn/sac').agg({
                'Invoice Amount': 'sum',
                'Total Tax Amount': 'sum',
                'Quantity': 'sum'
            }).round(2)
            
            # TCS analysis
            tcs_columns = ['Tcs Igst Amount', 'Tcs Cgst Amount', 'Tcs Sgst Amount', 'Tcs Utgst Amount']
            tcs_data = []
            for col in tcs_columns:
                if col in shipments.columns:
                    tcs_data.append(shipments[col].sum())
            analysis['total_tcs'] = sum(tcs_data)
        
        return analysis
    
    def create_comparison_dashboard(self):
        """Create comparison dashboard across platforms"""
        comparisons = {}
        
        # Meesho analysis
        meesho_analysis = self.analyze_meesho_data()
        if meesho_analysis:
            comparisons['Meesho'] = {
                'Sales': meesho_analysis['total_sales'],
                'Tax': meesho_analysis['total_tax'],
                'Orders': meesho_analysis['total_orders']
            }
        
        # Amazon analysis
        amazon_analysis = self.analyze_amazon_data()
        if amazon_analysis:
            comparisons['Amazon'] = {
                'Sales': amazon_analysis.get('total_sales', 0),
                'Tax': amazon_analysis.get('total_tax', 0),
                'Orders': amazon_analysis.get('total_shipments', 0)
            }
        
        # Flipkart analysis (basic - structure depends on actual data)
        if self.flipkart_data is not None and not self.flipkart_data.empty:
            comparisons['Flipkart'] = {
                'Sales': 0,  # Would need actual column mapping
                'Tax': 0,
                'Orders': len(self.flipkart_data)
            }
        
        return comparisons

def main():
    st.markdown('<h1 class="main-header">🛒 Multi-Platform E-commerce Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    analyzer = EcommerceAnalyzer()
    
    # Sidebar for file uploads
    st.sidebar.header("📁 Upload Data Files")
    
    # Meesho files
    st.sidebar.subheader("Meesho Data")
    meesho_sales_file = st.sidebar.file_uploader("Upload Meesho Sales Data", type=['csv'], key="meesho_sales")
    meesho_returns_file = st.sidebar.file_uploader("Upload Meesho Returns Data (Optional)", type=['csv'], key="meesho_returns")
    
    # Amazon files
    st.sidebar.subheader("Amazon Data")
    amazon_file = st.sidebar.file_uploader("Upload Amazon MTR Report", type=['csv'], key="amazon")
    
    # Flipkart files
    st.sidebar.subheader("Flipkart Data")
    flipkart_file = st.sidebar.file_uploader("Upload Flipkart GSTR-1 Report", type=['csv'], key="flipkart")
    
    # Load data
    data_loaded = False
    
    if meesho_sales_file:
        if analyzer.load_meesho_data(meesho_sales_file, meesho_returns_file):
            data_loaded = True
    
    if amazon_file:
        if analyzer.load_amazon_data(amazon_file):
            data_loaded = True
    
    if flipkart_file:
        if analyzer.load_flipkart_data(flipkart_file):
            data_loaded = True
    
    if not data_loaded:
        st.info("👆 Please upload at least one data file to begin analysis")
        return
    
    # Create tabs for different analyses
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "🛍️ Meesho Analysis", "📦 Amazon Analysis", "🏪 Flipkart Analysis", "📈 Comparison"])
    
    with tab1:
        st.header("📊 Platform Overview")
        
        # Platform comparison
        comparisons = analyzer.create_comparison_dashboard()
        
        if comparisons:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Platforms", len(comparisons))
            
            total_sales = sum([comp.get('Sales', 0) for comp in comparisons.values()])
            total_tax = sum([comp.get('Tax', 0) for comp in comparisons.values()])
            total_orders = sum([comp.get('Orders', 0) for comp in comparisons.values()])
            
            with col2:
                st.metric("Total Sales", f"₹{total_sales:,.2f}")
            
            with col3:
                st.metric("Total Tax", f"₹{total_tax:,.2f}")
            
            # Platform-wise metrics
            if len(comparisons) > 1:
                df_comparison = pd.DataFrame(comparisons).T
                df_comparison = df_comparison.fillna(0)
                
                fig = px.bar(df_comparison, 
                           title="Platform-wise Sales Comparison",
                           labels={'value': 'Amount (₹)', 'index': 'Platform'})
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("🛍️ Meesho Analysis")
        
        meesho_analysis = analyzer.analyze_meesho_data()
        
        if meesho_analysis:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Orders", f"{meesho_analysis['total_orders']:,}")
            
            with col2:
                st.metric("Total Sales", f"₹{meesho_analysis['total_sales']:,.2f}")
            
            with col3:
                st.metric("Total Tax", f"₹{meesho_analysis['total_tax']:,.2f}")
            
            with col4:
                tax_rate = (meesho_analysis['total_tax'] / meesho_analysis['total_sales']) * 100
                st.metric("Avg Tax Rate", f"{tax_rate:.2f}%")
            
            # State-wise analysis
            st.subheader("State-wise Performance")
            state_data = meesho_analysis['state_wise'].sort_values('total_invoice_value', ascending=False)
            
            fig = px.bar(state_data, 
                        x=state_data.index, 
                        y='total_invoice_value',
                        title="State-wise Sales Distribution",
                        labels={'total_invoice_value': 'Sales (₹)', 'index': 'State'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Tax rate analysis
            st.subheader("Tax Rate Analysis")
            tax_rate_data = meesho_analysis['tax_rate_analysis']
            
            fig = px.pie(tax_rate_data, 
                        values='total_invoice_value', 
                        names=tax_rate_data.index,
                        title="Sales Distribution by Tax Rate")
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed tables
            st.subheader("Detailed Data")
            
            tab_states, tab_products, tab_tax = st.tabs(["States", "Products", "Tax Rates"])
            
            with tab_states:
                st.dataframe(state_data)
            
            with tab_products:
                st.dataframe(meesho_analysis['product_performance'])
            
            with tab_tax:
                st.dataframe(tax_rate_data)
        
        else:
            st.info("No Meesho data available for analysis")
    
    with tab3:
        st.header("📦 Amazon Analysis")
        
        amazon_analysis = analyzer.analyze_amazon_data()
        
        if amazon_analysis:
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Shipments", f"{amazon_analysis['total_shipments']:,}")
            
            with col2:
                st.metric("Total Sales", f"₹{amazon_analysis.get('total_sales', 0):,.2f}")
            
            with col3:
                st.metric("Total Tax", f"₹{amazon_analysis.get('total_tax', 0):,.2f}")
            
            with col4:
                st.metric("TCS Amount", f"₹{amazon_analysis.get('total_tcs', 0):,.2f}")
            
            # Returns and cancellations
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Refunds", f"{amazon_analysis['total_refunds']:,}")
            
            with col2:
                st.metric("Total Cancellations", f"{amazon_analysis['total_cancellations']:,}")
            
            with col3:
                if amazon_analysis['total_shipments'] > 0:
                    return_rate = (amazon_analysis['total_refunds'] / amazon_analysis['total_shipments']) * 100
                    st.metric("Return Rate", f"{return_rate:.2f}%")
            
            # State-wise analysis
            if 'state_wise' in amazon_analysis:
                st.subheader("State-wise Performance")
                state_data = amazon_analysis['state_wise'].sort_values('Invoice Amount', ascending=False)
                
                fig = px.bar(state_data, 
                            x=state_data.index, 
                            y='Invoice Amount',
                            title="State-wise Sales Distribution",
                            labels={'Invoice Amount': 'Sales (₹)', 'index': 'State'})
                st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(state_data)
        
        else:
            st.info("No Amazon data available for analysis")
    
    with tab4:
        st.header("🏪 Flipkart Analysis")
        
        if analyzer.flipkart_data is not None:
            st.subheader("Flipkart Data Overview")
            
            # Basic info about the data
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Records", len(analyzer.flipkart_data))
            
            with col2:
                st.metric("Columns", len(analyzer.flipkart_data.columns))
            
            # Display data structure
            st.subheader("Data Structure")
            st.dataframe(analyzer.flipkart_data.head())
            
            # Column information
            st.subheader("Column Information")
            st.write(analyzer.flipkart_data.dtypes)
            
        else:
            st.info("No Flipkart data available for analysis")
    
    with tab5:
        st.header("📈 Platform Comparison")
        
        comparisons = analyzer.create_comparison_dashboard()
        
        if len(comparisons) > 1:
            df_comparison = pd.DataFrame(comparisons).T
            df_comparison = df_comparison.fillna(0)
            
            # Sales comparison
            fig = px.bar(df_comparison, 
                        y=df_comparison.index, 
                        x='Sales',
                        orientation='h',
                        title="Sales Comparison Across Platforms",
                        labels={'Sales': 'Sales (₹)', 'index': 'Platform'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Tax comparison
            fig = px.bar(df_comparison, 
                        y=df_comparison.index, 
                        x='Tax',
                        orientation='h',
                        title="Tax Comparison Across Platforms",
                        labels={'Tax': 'Tax (₹)', 'index': 'Platform'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary table
            st.subheader("Summary Table")
            st.dataframe(df_comparison)
            
            # Insights
            st.subheader("Key Insights")
            
            total_sales = df_comparison['Sales'].sum()
            best_platform = df_comparison['Sales'].idxmax()
            best_platform_sales = df_comparison.loc[best_platform, 'Sales']
            
            st.write(f"• **Best performing platform:** {best_platform} with ₹{best_platform_sales:,.2f} in sales")
            st.write(f"• **Total sales across all platforms:** ₹{total_sales:,.2f}")
            
            if total_sales > 0:
                best_platform_share = (best_platform_sales / total_sales) * 100
                st.write(f"• **{best_platform} market share:** {best_platform_share:.1f}%")
        
        else:
            st.info("Upload data from multiple platforms to see comparisons")
    
    # Footer
    st.markdown("---")
    st.markdown("**E-commerce Analytics Dashboard** | Built with Streamlit")

if __name__ == "__main__":
    main()