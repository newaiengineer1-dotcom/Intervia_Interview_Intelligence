st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root{
 --bg:#070B16;
 --bg2:#0B1020;
 --panel:#10172B;
 --panel2:#131D34;
 --panel3:#0F172A;

 --line:#1E293B;
 --line2:#334155;

 --text:#F8FAFC;
 --text2:#CBD5E1;
 --muted:#64748B;
 --muted2:#94A3B8;

 --purple:#7C6DFF;
 --purple2:#A78BFA;
 --violet:#8B5CF6;
 --indigo:#6366F1;

 --cyan:#67E8F9;
 --cyan2:#22D3EE;

 --green:#10B981;
 --yellow:#FBBF24;
 --red:#EF4444;

 --glass:rgba(20,28,48,.72);
}

*{
 box-sizing:border-box;
}

html,
body{
 background:#070B16!important;
 font-family:'Inter',sans-serif!important;
}

.stApp{
 background:
 radial-gradient(circle at top left,
 rgba(124,109,255,.12),
 transparent 30%),
 radial-gradient(circle at top right,
 rgba(34,211,238,.08),
 transparent 28%),
 #070B16 !important;

 color:var(--text)!important;
 font-family:'Inter',sans-serif!important;
}

.block-container{
 max-width:1600px!important;
 padding:12px 18px 22px!important;
}

header{
 visibility:hidden;
}

footer{
 visibility:hidden;
}

[data-testid="stSidebar"]{
 background:
 linear-gradient(
 180deg,
 #08101F 0%,
 #0B1120 100%
 ) !important;

 border-right:1px solid rgba(124,109,255,.15)!important;

 box-shadow:
 inset -1px 0 0 rgba(255,255,255,.04),
 10px 0 40px rgba(0,0,0,.35);
}

[data-testid="stSidebar"] *{
 color:#CBD5E1;
}

/* Top Bar */

.topbar{
 display:flex;
 justify-content:space-between;
 align-items:center;
 margin-bottom:12px;

 border-bottom:1px solid rgba(255,255,255,.06);
 padding:6px 0 12px;
}

.brand{
 font-size:18px;
 font-weight:800;
 color:white;
}

.brand span{
 color:#A78BFA;
}

.crumb{
 color:#94A3B8;
 font-size:11px;
}

/* Navigation */

.navrow{
 background:#0D152A;
 border:1px solid rgba(255,255,255,.04);
 border-radius:18px;
 padding:8px;
 display:grid;
 grid-template-columns:repeat(6,1fr);
 gap:8px;
 margin-bottom:18px;
}

.navpill{
 text-align:center;
 padding:10px;
 border-radius:12px;
 color:#94A3B8;
 font-size:11px;
 font-weight:600;
}

.navpill.active{
 background:
 linear-gradient(
 135deg,
 #7C6DFF,
 #9B8CFF
 );

 color:#FFF;

 box-shadow:
 0 0 30px rgba(124,109,255,.45),
 0 6px 20px rgba(124,109,255,.25);
}

/* Hero */

.hero2{
 background:
 linear-gradient(
 135deg,
 rgba(124,109,255,.18),
 rgba(34,211,238,.04)
 );

 border:1px solid rgba(124,109,255,.18);

 backdrop-filter:blur(20px);

 border-radius:24px;

 padding:30px;

 box-shadow:
 0 20px 50px rgba(0,0,0,.30);

 margin-bottom:16px;
}

.hero2 h1{
 color:white;
 font-weight:800;
}

.subhero{
 color:#CBD5E1;
}

/* Panels */

.panel{
 background:rgba(16,23,43,.82);

 backdrop-filter:blur(18px);
 -webkit-backdrop-filter:blur(18px);

 border:1px solid rgba(124,109,255,.12);

 border-radius:22px;

 box-shadow:
 0 10px 40px rgba(0,0,0,.35),
 inset 0 1px 0 rgba(255,255,255,.04);

 padding:22px!important;
 margin-bottom:16px!important;
}

.panel-title{
 color:#FFF;
 font-weight:800;
 letter-spacing:.08em;
 text-transform:uppercase;
}

/* Chips */

.chip{
 padding:6px 12px;
 border-radius:999px;
 background:#151E34;
 border:1px solid #233252;
 color:#CBD5E1;
 font-size:10px;
 margin-left:5px;
}

.chip.green{
 color:#34D399;
 border:1px solid rgba(52,211,153,.35);
 background:rgba(52,211,153,.10);
}

.chip.red{
 color:#F87171;
 border:1px solid rgba(248,113,113,.35);
 background:rgba(248,113,113,.10);
}

.chip.lav{
 color:#C4B5FD;
 border:1px solid rgba(167,139,250,.25);
 background:rgba(167,139,250,.12);
}

/* Metric */

.metric-card{
 background:
 linear-gradient(
 180deg,
 rgba(20,28,48,.92),
 rgba(13,19,36,.98)
 );

 border:1px solid rgba(124,109,255,.10);

 border-radius:18px;

 backdrop-filter:blur(12px);

 min-height:90px!important;

 box-shadow:
 0 8px 30px rgba(0,0,0,.25);

 padding:15px;
}

.metric-k{
 color:#94A3B8;
 font-size:10px;
 text-transform:uppercase;
}

.metric-v{
 font-size:28px!important;
 font-weight:800!important;

 background:
 linear-gradient(
 135deg,
 #A78BFA,
 #67E8F9
 );

 -webkit-background-clip:text;
 -webkit-text-fill-color:transparent;
}

.metric-s{
 color:#94A3B8;
 font-size:11px;
}

/* Question */

.question-card{
 background:
 linear-gradient(
 180deg,
 #131D34,
 #0F172A
 );

 border:1px solid rgba(124,109,255,.18);

 border-radius:24px;

 padding:26px!important;

 box-shadow:
 0 12px 40px rgba(0,0,0,.35);

 position:relative;
}

.question-card::before{
 content:"";
 position:absolute;
 top:0;
 left:0;
 right:0;
 height:2px;

 background:
 linear-gradient(
 90deg,
 #7C6DFF,
 #22D3EE
 );
}

.question-card .q{
 color:white;
 font-weight:700;
 font-size:22px;
}

.category-pill{
 display:inline-block;
 padding:6px 11px;
 border-radius:999px;
 border:1px solid rgba(124,109,255,.4);
 color:#C4B5FD;
 background:rgba(124,109,255,.14);
 font-size:10px;
}

/* Buttons */

div[data-testid="stButton"]>button,
.stDownloadButton>button{

 background:
 linear-gradient(
 135deg,
 #7C6DFF,
 #67C8FF
 ) !important;

 color:white!important;

 border:none!important;

 border-radius:16px!important;

 font-weight:700!important;

 box-shadow:
 0 10px 25px rgba(124,109,255,.35);

 transition:.3s;
}

div[data-testid="stButton"]>button:hover,
.stDownloadButton>button:hover{

 transform:translateY(-2px);

 box-shadow:
 0 0 30px rgba(124,109,255,.45);
}

/* Progress */

.stProgress > div > div > div{
 background:
 linear-gradient(
 90deg,
 #46E5B9,
 #67E8F9,
 #7C6DFF
 ) !important;

 box-shadow:
 0 0 15px rgba(103,232,249,.45);

 border-radius:999px!important;
}

/* Status */

.status-badge.active{
 animation:pulseGlow 2s infinite;
 border-color:#7C6DFF;
 color:#C4B5FD;
 background:rgba(124,109,255,.12);
}

@keyframes pulseGlow{
 0%{
  box-shadow:0 0 0 rgba(124,109,255,0);
 }
 50%{
  box-shadow:0 0 18px rgba(124,109,255,.45);
 }
 100%{
  box-shadow:0 0 0 rgba(124,109,255,0);
 }
}

/* Glassmorphism */

.panel,
.metric-card,
.question-card,
.score-ring,
.evidence-kpi{
 backdrop-filter:blur(14px);
 -webkit-backdrop-filter:blur(14px);
}

.question-card:hover,
.metric-card:hover,
.panel:hover{
 transition:.3s ease;
 box-shadow:
 0 0 35px rgba(124,109,255,.15),
 0 10px 40px rgba(0,0,0,.35);
}

</style>
""", unsafe_allow_html=True)
