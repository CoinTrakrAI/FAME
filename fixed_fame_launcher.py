#!/usr/bin/env python3
"""
Fixed F.A.M.E. Launcher with proper async handling
"""

import asyncio
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("[WARNING] tkinter not available. GUI disabled.")

import threading
from datetime import datetime

# Import the fixed enhanced modules
try:
    from core.enhanced_market_oracle import EnhancedMarketOracle
    ORACLE_AVAILABLE = True
except ImportError as e:
    print(f"[WARNING] EnhancedMarketOracle not available: {e}")
    ORACLE_AVAILABLE = False


def log_to_console(message: str):
    """Log to console if GUI not available"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


if TKINTER_AVAILABLE:
    class FixedFAMELauncher:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title("F.A.M.E. - FIXED Working System")
            self.root.geometry("1200x800")
            
            # Initialize systems
            self.systems = {}
            if ORACLE_AVAILABLE:
                self.systems['market_oracle'] = EnhancedMarketOracle()
            
            self.setup_interface()
            
        def setup_interface(self):
            # Simplified interface setup
            self.notebook = ttk.Notebook(self.root)
            self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Market Analysis Tab
            market_frame = ttk.Frame(self.notebook)
            self.notebook.add(market_frame, text="Market Analysis")
            
            tk.Label(market_frame, text="Stock Symbol:").pack(pady=5)
            self.symbol_entry = tk.Entry(market_frame)
            self.symbol_entry.pack(pady=5)
            self.symbol_entry.insert(0, "AAPL")
            
            analyze_btn = tk.Button(market_frame, text="Analyze", command=self.analyze_stock)
            analyze_btn.pack(pady=5)
            
            self.analysis_text = scrolledtext.ScrolledText(market_frame, height=20)
            self.analysis_text.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Console
            self.console = scrolledtext.ScrolledText(self.root, height=10)
            self.console.pack(fill='x', padx=10, pady=5)
            
        def log_message(self, message: str):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.console.insert(tk.END, f"[{timestamp}] {message}\n")
            self.console.see(tk.END)
            self.root.update()
            
        def analyze_stock(self):
            if not ORACLE_AVAILABLE:
                messagebox.showerror("Error", "Market Oracle not available")
                return
                
            symbol = self.symbol_entry.get().strip().upper()
            if not symbol:
                messagebox.showerror("Error", "Please enter a stock symbol")
                return
                
            self.log_message(f"Analyzing {symbol}...")
            
            def run_analysis():
                try:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def analyze():
                        async with self.systems['market_oracle'] as oracle:
                            return await oracle.get_enhanced_market_analysis(symbol)
                    
                    result = loop.run_until_complete(analyze())
                    loop.close()
                    
                    # Update UI in main thread
                    self.root.after(0, lambda: self.display_analysis_result(result))
                    
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"Error: {str(e)}"))
            
            threading.Thread(target=run_analysis, daemon=True).start()
            
        def display_analysis_result(self, result):
            self.analysis_text.delete(1.0, tk.END)
            
            if "error" in result:
                self.analysis_text.insert(tk.END, f"Error: {result['error']}\n")
                self.log_message("Analysis failed")
                return
                
            self.analysis_text.insert(tk.END, f"Analysis for {result.get('symbol', 'N/A')}\n")
            self.analysis_text.insert(tk.END, "=" * 50 + "\n\n")
            self.analysis_text.insert(tk.END, f"Current Price: ${result.get('current_price', 'N/A')}\n")
            
            # AI Prediction
            ai_pred = result.get('ai_prediction', {})
            self.analysis_text.insert(tk.END, f"AI Prediction: {ai_pred.get('predicted_direction', 'N/A')}\n")
            self.analysis_text.insert(tk.END, f"Confidence: {ai_pred.get('confidence', 0):.1%}\n\n")
            
            # Technical Signals
            technicals = result.get('technical_analysis', {})
            signals = technicals.get('signals', [])
            self.analysis_text.insert(tk.END, f"Signals: {', '.join(signals)}\n")
            
            self.log_message("Analysis completed successfully")
    
    def main():
        if not TKINTER_AVAILABLE:
            log_to_console("GUI not available. Please install tkinter.")
            return
            
        app = FixedFAMELauncher()
        app.root.mainloop()

else:
    # Console-only mode
    async def console_analyze(symbol: str):
        """Console version of stock analysis"""
        if not ORACLE_AVAILABLE:
            log_to_console("Market Oracle not available")
            return
            
        log_to_console(f"Analyzing {symbol}...")
        try:
            async with EnhancedMarketOracle() as oracle:
                result = await oracle.get_enhanced_market_analysis(symbol)
                
                if "error" in result:
                    log_to_console(f"Error: {result['error']}")
                    return
                
                log_to_console(f"\n=== Analysis for {result.get('symbol', 'N/A')} ===")
                log_to_console(f"Current Price: ${result.get('current_price', 'N/A')}")
                
                ai_pred = result.get('ai_prediction', {})
                log_to_console(f"AI Prediction: {ai_pred.get('predicted_direction', 'N/A')}")
                log_to_console(f"Confidence: {ai_pred.get('confidence', 0):.1%}")
                
                technicals = result.get('technical_analysis', {})
                signals = technicals.get('signals', [])
                log_to_console(f"Signals: {', '.join(signals)}")
                
        except Exception as e:
            log_to_console(f"Error: {str(e)}")
    
    def main():
        import sys
        symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
        asyncio.run(console_analyze(symbol))


if __name__ == "__main__":
    main()

