"""
Streamlit UI for Google Shopping Agent
"""
import streamlit as st
import asyncio
import json
import os
from datetime import datetime
from typing import Optional, List
import pandas as pd

# Page config must be first Streamlit command
st.set_page_config(
    page_title="HarbiFırsat Shopping Agent",
    page_icon="🛒",
    layout="wide"
)

# Import agent components
from config import SerpApiConfig, SupabaseConfig
from models import SearchQuery, ShoppingProduct, DealToCreate, DealStatus
from serp_api_client import SerpApiClient
from supabase_client import HarbiSupabaseClient


def init_session_state():
    """Initialize session state variables"""
    if 'products' not in st.session_state:
        st.session_state.products = []
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'serp_client_config' not in st.session_state:
        st.session_state.serp_client_config = None
    if 'supabase_client' not in st.session_state:
        st.session_state.supabase_client = None
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = set()
    if 'quick_searches' not in st.session_state:
        st.session_state.quick_searches = []


def render_sidebar():
    """Render sidebar with configuration"""
    st.sidebar.title("⚙️ Configuration")
    
    # SERP API Configuration
    st.sidebar.subheader("🔍 SERP API")
    serp_api_key = st.sidebar.text_input(
        "API Key",
        type="password",
        value=os.environ.get("SERP_API_KEY", ""),
        help="Get your API key from serpapi.com"
    )
    
    # Country/Language settings
    col1, col2 = st.sidebar.columns(2)
    with col1:
        country = st.selectbox(
            "Country",
            ["tr", "us", "uk", "de", "fr"],
            index=0,
            help="Google Shopping country"
        )
    with col2:
        language = st.selectbox(
            "Language", 
            ["tr", "en", "de", "fr"],
            index=0,
            help="Search language"
        )
    
    # Supabase Configuration
    st.sidebar.subheader("🗄️ Supabase")
    supabase_url = st.sidebar.text_input(
        "Supabase URL",
        value=os.environ.get("SUPABASE_URL", ""),
        help="Your Supabase project URL"
    )
    supabase_key = st.sidebar.text_input(
        "Supabase Key",
        type="password",
        value=os.environ.get("SUPABASE_ANON_KEY", ""),
        help="Your Supabase anon/service key"
    )
    
    # Store configuration in session state
    if serp_api_key:
        st.session_state.serp_client_config = SerpApiConfig(
            api_key=serp_api_key,
            country=country,
            language=language
        )
    
    # Initialize Supabase client
    if supabase_url and supabase_key:
        try:
            supabase_config = SupabaseConfig(
                url=supabase_url,
                anon_key=supabase_key
            )
            st.session_state.supabase_client = HarbiSupabaseClient(supabase_config).connect()
            st.sidebar.success("✅ Supabase bağlandı")
            
            # Load quick searches from Supabase
            if not st.session_state.quick_searches:
                load_quick_searches()
                
        except Exception as e:
            st.sidebar.error(f"❌ Supabase hatası: {e}")
    
    return {
        'serp_api_key': serp_api_key,
        'country': country,
        'language': language,
        'supabase_url': supabase_url,
        'supabase_key': supabase_key
    }


def load_quick_searches():
    """Load most popular keywords from Supabase deal_alerts (by alarm count)"""
    if st.session_state.supabase_client:
        try:
            # Call the aggregated function - returns only keyword + count (safe)
            response = st.session_state.supabase_client.client.rpc(
                'get_popular_keywords',
                {'limit_count': 6}
            ).execute()
            
            if response.data:
                st.session_state.quick_searches = [
                    item['keyword'] for item in response.data if item.get('keyword')
                ]
            else:
                st.session_state.quick_searches = []
        except Exception as e:
            st.sidebar.error(f"Arama yüklenemedi: {e}")
            st.session_state.quick_searches = []


async def search_products(
    query: str,
    config: SerpApiConfig,
    min_discount: float = 0,
    on_sale: bool = True,
    sort_by: str = None,
    min_rating: float = None
) -> list[ShoppingProduct]:
    """Search for products using SERP API"""
    search_query = SearchQuery(
        keyword=query,
        on_sale=on_sale,
        sort_by=sort_by,
        min_rating=min_rating
    )
    
    async with SerpApiClient(config) as client:
        if min_discount > 0:
            products = await client.search_with_discount_filter(
                search_query,
                min_discount=min_discount
            )
        else:
            products = await client.search(search_query)
    
    # Filter by rating if specified
    if min_rating:
        products = [p for p in products if p.rating and p.rating >= min_rating]
    
    return products


def get_currency_symbol(country: str) -> str:
    """Get currency symbol based on country code"""
    currency_map = {
        'tr': '₺',
        'us': '$',
        'uk': '£',
        'de': '€',
        'fr': '€',
        'es': '€',
        'it': '€',
        'nl': '€',
        'jp': '¥',
        'kr': '₩',
        'cn': '¥',
        'in': '₹',
        'br': 'R$',
        'au': 'A$',
        'ca': 'C$',
    }
    return currency_map.get(country, '$')


def render_product_card(product: ShoppingProduct, index: int, currency: str = '₺', selectable: bool = False):
    """Render a single product card"""
    product_key = product.product_id or str(index)
    
    with st.container():
        cols = st.columns([0.5, 1, 3, 1]) if selectable else st.columns([1, 3, 1])
        col_offset = 0
        
        if selectable:
            with cols[0]:
                is_selected = st.checkbox(
                    "Seç",
                    key=f"select_{product_key}",
                    value=product_key in st.session_state.selected_products,
                    label_visibility="collapsed"
                )
                if is_selected:
                    st.session_state.selected_products.add(product_key)
                else:
                    st.session_state.selected_products.discard(product_key)
            col_offset = 1
        
        with cols[col_offset]:
            if product.thumbnail:
                st.image(product.thumbnail, width=100)
            else:
                st.write("🖼️ No image")
        
        with cols[col_offset + 1]:
            st.markdown(f"**{product.title[:80]}...**" if len(product.title) > 80 else f"**{product.title}**")
            st.write(f"🏪 {product.source}")
            
            # Price display
            discount = product.calculate_discount_percentage()
            if discount and discount > 0:
                st.markdown(
                    f"💰 **{currency}{product.price:.2f}** "
                    f"~~{currency}{product.original_price:.2f}~~ "
                    f"<span style='color: green; font-weight: bold;'>-{discount:.0f}%</span>",
                    unsafe_allow_html=True
                )
            else:
                st.write(f"💰 **{currency}{product.price:.2f}**")
            
            # Rating
            if product.rating:
                stars = "⭐" * int(product.rating)
                st.write(f"{stars} {product.rating}/5 ({product.reviews or 0} reviews)")
        
        with cols[col_offset + 2]:
            if product.product_link:
                st.link_button("🔗 View", product.product_link)
            
            if product.discount_tag:
                st.success(product.discount_tag)
        
        st.divider()


def render_products_table(products: list[ShoppingProduct], currency: str = '₺'):
    """Render products as a dataframe table"""
    if not products:
        st.info("No products to display")
        return
    
    data = []
    for p in products:
        data.append({
            "Title": p.title[:60] + "..." if len(p.title) > 60 else p.title,
            "Store": p.source,
            "Price": f"{currency}{p.price:.2f}",
            "Original": f"{currency}{p.original_price:.2f}" if p.original_price else "-",
            "Discount": f"{p.calculate_discount_percentage():.0f}%" if p.calculate_discount_percentage() else "-",
            "Rating": f"{p.rating}/5" if p.rating else "-",
            "Reviews": p.reviews or 0
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def send_to_approval(selected_products: List[ShoppingProduct]):
    """Send selected products to Supabase for admin approval"""
    if not st.session_state.supabase_client:
        st.error("Supabase bağlantısı yok!")
        return 0
    
    client = st.session_state.supabase_client
    count = 0
    
    for product in selected_products:
        try:
            # Create deal for approval
            deal_data = {
                'title': product.title,
                'description': f"Google Shopping'den bulunan ürün. Mağaza: {product.source}",
                'price': product.price,
                'original_price': product.original_price,
                'discount_percentage': product.calculate_discount_percentage(),
                'url': product.product_link,
                'image_url': product.thumbnail,
                'source': 'google_shopping',
                'store_name': product.source,
                'status': 'pending',  # Admin onayı bekliyor
                'external_id': product.product_id,
                'rating': product.rating,
                'reviews_count': product.reviews,
                'created_at': datetime.now().isoformat()
            }
            
            # Insert into deals table with pending status
            response = client.client.table('deals').insert(deal_data).execute()
            
            if response.data:
                count += 1
                
        except Exception as e:
            st.warning(f"Ürün eklenemedi: {product.title[:30]}... - {e}")
    
    return count


def main():
    """Main Streamlit app"""
    init_session_state()
    
    # Header
    st.title("🛒 HarbiFırsat Google Shopping Agent")
    st.markdown("İndirimli ürünleri ara ve admin onayına gönder")
    
    # Sidebar configuration
    config = render_sidebar()
    
    # Main content tabs
    tab1, tab2 = st.tabs(["🔍 Search", "📋 Results"])
    
    with tab1:
        st.subheader("Search Google Shopping")
        
        # Check for quick search from button
        if 'quick_search' in st.session_state:
            default_query = st.session_state.pop('quick_search')
        else:
            default_query = ""
        
        # Search form
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Search Query",
                value=default_query,
                placeholder="e.g., iPhone 15, Nike shoes, Samsung TV..."
            )
        
        with col2:
            min_discount = st.number_input(
                "Min Discount %",
                min_value=0,
                max_value=90,
                value=10,
                step=5
            )
        
        col3, col4, col5 = st.columns(3)
        
        with col3:
            on_sale = st.checkbox("On Sale Only", value=True)
        
        with col4:
            sort_options = {
                "En İyi Sonuçlar (Önerilen)": None,
                "Fiyat: Düşükten Yükseğe": "1",
                "Fiyat: Yüksekten Düşüğe": "2"
            }
            sort_label = st.selectbox("Sıralama", list(sort_options.keys()), index=0)
            sort_by = sort_options[sort_label]
        
        with col5:
            min_rating = st.selectbox(
                "Min Rating",
                [None, 3.0, 3.5, 4.0, 4.5],
                index=0,
                format_func=lambda x: "Tümü" if x is None else f"⭐ {x}+"
            )
        
        col6, col7 = st.columns(2)
        
        with col6:
            max_results = st.selectbox("Max Results", [20, 40, 60, 100], index=1)
        
        # Search button
        search_button = st.button("🔍 Search", type="primary", use_container_width=True)
        
        if search_button:
            if not config['serp_api_key']:
                st.error("❌ Please enter your SERP API key in the sidebar")
                return
            
            if not search_query:
                st.warning("Please enter a search query")
                return
            
            with st.spinner(f"Searching for '{search_query}'..."):
                try:
                    # Clear previous selections
                    st.session_state.selected_products = set()
                    
                    # Run async search
                    products = asyncio.run(search_products(
                        query=search_query,
                        config=st.session_state.serp_client_config,
                        min_discount=min_discount,
                        on_sale=on_sale,
                        sort_by=sort_by,
                        min_rating=min_rating
                    ))
                    
                    st.session_state.products = products
                    
                    # Add to search history
                    st.session_state.search_history.append({
                        'query': search_query,
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'results': len(products)
                    })
                    
                    st.success(f"✅ Found {len(products)} products!")
                    
                except Exception as e:
                    st.error(f"❌ Search failed: {e}")
        
        # Quick search buttons
        st.subheader("🏷️ Quick Searches")
        
        # Use Supabase categories or fallback
        quick_searches = st.session_state.quick_searches if st.session_state.quick_searches else [
            "Elektronik", "Moda", "Ev & Yaşam", "Spor", "Kozmetik", "Oyun"
        ]
        
        if quick_searches:
            cols = st.columns(min(len(quick_searches), 6))
            for i, qs in enumerate(quick_searches[:6]):
                with cols[i]:
                    if st.button(qs, key=f"quick_{i}"):
                        st.session_state['quick_search'] = qs
                        st.rerun()
        
        # Reload button for quick searches
        if st.session_state.supabase_client:
            if st.button("🔄 Popüler aramaları yenile"):
                st.session_state.quick_searches = []  # Clear first
                load_quick_searches()
                st.success(f"✅ {len(st.session_state.quick_searches)} popüler arama yüklendi")
                st.rerun()
        
        # Search history
        if st.session_state.search_history:
            st.subheader("🕐 Recent Searches")
            for item in reversed(st.session_state.search_history[-5:]):
                st.write(f"• {item['query']} ({item['results']} results) - {item['timestamp']}")
    
    with tab2:
        st.subheader("Search Results")
        
        if not st.session_state.products:
            st.info("No products yet. Run a search to see results.")
        else:
            # Selection info and action buttons
            col_info, col_action = st.columns([2, 1])
            
            with col_info:
                selected_count = len(st.session_state.selected_products)
                if selected_count > 0:
                    st.info(f"📦 {selected_count} ürün seçildi")
            
            with col_action:
                if st.button("📤 Seçilenleri Onaya Gönder", type="primary", disabled=selected_count == 0):
                    if not st.session_state.supabase_client:
                        st.error("Supabase bağlantısı gerekli!")
                    else:
                        # Get selected products
                        selected = []
                        for p in st.session_state.products:
                            key = p.product_id or str(st.session_state.products.index(p))
                            if key in st.session_state.selected_products:
                                selected.append(p)
                        
                        if selected:
                            with st.spinner("Ürünler admin onayına gönderiliyor..."):
                                count = send_to_approval(selected)
                                if count > 0:
                                    st.success(f"✅ {count} ürün admin onayına gönderildi!")
                                    st.session_state.selected_products = set()
                                    st.rerun()
            
            # Select all / Deselect all
            col_sel1, col_sel2, col_sel3 = st.columns([1, 1, 4])
            with col_sel1:
                if st.button("✅ Tümünü Seç"):
                    for i, p in enumerate(st.session_state.products):
                        key = p.product_id or str(i)
                        st.session_state.selected_products.add(key)
                    st.rerun()
            with col_sel2:
                if st.button("❌ Seçimi Kaldır"):
                    st.session_state.selected_products = set()
                    st.rerun()
            
            st.divider()
            
            # Filter controls
            col1, col2 = st.columns(2)
            with col1:
                sort_by_result = st.selectbox("Sort by", ["Discount %", "Price (Low)", "Price (High)", "Rating"], key="sort_results")
            with col2:
                filter_discount = st.slider("Min Discount Filter", 0, 90, 0)
            
            # Apply filters
            products = st.session_state.products
            
            if filter_discount > 0:
                products = [p for p in products if (p.calculate_discount_percentage() or 0) >= filter_discount]
            
            # Apply sorting
            if sort_by_result == "Discount %":
                products = sorted(products, key=lambda x: x.calculate_discount_percentage() or 0, reverse=True)
            elif sort_by_result == "Price (Low)":
                products = sorted(products, key=lambda x: x.price)
            elif sort_by_result == "Price (High)":
                products = sorted(products, key=lambda x: x.price, reverse=True)
            elif sort_by_result == "Rating":
                products = sorted(products, key=lambda x: x.rating or 0, reverse=True)
            
            st.write(f"Showing {len(products)} products")
            
            # Get currency symbol based on country
            currency = get_currency_symbol(config.get('country', 'tr'))
            
            # Render products with selection
            for i, product in enumerate(products):
                render_product_card(product, i, currency, selectable=True)
            
            # Export buttons
            st.subheader("📥 Export")
            
            # Prepare export data
            if products:
                export_data = []
                for p in products:
                    export_data.append({
                        "Title": p.title,
                        "Store": p.source,
                        "Price": f"{currency}{p.price:.2f}",
                        "Original Price": f"{currency}{p.original_price:.2f}" if p.original_price else "",
                        "Discount %": p.calculate_discount_percentage() or "",
                        "Rating": p.rating or "",
                        "Reviews": p.reviews or "",
                        "Link": p.product_link or ""
                    })
                df = pd.DataFrame(export_data)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # CSV export
                if products:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "📥 CSV",
                        csv,
                        "products.csv",
                        "text/csv",
                        help="Simple format, opens in Excel"
                    )
            
            with col2:
                # Excel export
                if products:
                    import io
                    buffer = io.BytesIO()
                    df.to_excel(buffer, index=False, engine='openpyxl')
                    st.download_button(
                        "📗 Excel",
                        buffer.getvalue(),
                        "products.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        help="Native Excel format"
                    )
            
            with col3:
                # JSON export
                if products:
                    json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                    st.download_button(
                        "📋 JSON",
                        json_str,
                        "products.json",
                        "application/json",
                        help="For developers/APIs"
                    )


if __name__ == "__main__":
    main()
