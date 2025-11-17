import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import json
from pathlib import Path

# Try to import matplotlib (optional)
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    FigureCanvasTkAgg = None
    np = None

# Try to import docker (optional)
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None

import subprocess

class TrainingGUI:
    def __init__(self, parent):
        self.parent = parent
        self.training_active = False
        self.setup_gui()
        
    def setup_gui(self):
        """Setup training interface"""
        # Training controls
        control_frame = ttk.LabelFrame(self.parent, text="Training Controls", padding="10")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Model selection
        ttk.Label(control_frame, text="Model:").grid(row=0, column=0, sticky=tk.W)
        self.model_var = tk.StringVar(value="fame_living")
        model_combo = ttk.Combobox(control_frame, textvariable=self.model_var, 
                                  values=["fame_living", "voice_model", "market_predictor"])
        model_combo.grid(row=0, column=1, padx=5)
        
        # Training parameters
        ttk.Label(control_frame, text="Epochs:").grid(row=0, column=2, sticky=tk.W)
        self.epochs_var = tk.StringVar(value="100")
        ttk.Entry(control_frame, textvariable=self.epochs_var, width=10).grid(row=0, column=3, padx=5)
        
        ttk.Label(control_frame, text="Batch Size:").grid(row=0, column=4, sticky=tk.W)
        self.batch_var = tk.StringVar(value="32")
        ttk.Entry(control_frame, textvariable=self.batch_var, width=10).grid(row=0, column=5, padx=5)
        
        # Buttons
        ttk.Button(control_frame, text="Start Training", 
                  command=self.start_training).grid(row=0, column=6, padx=5)
        ttk.Button(control_frame, text="Stop Training", 
                  command=self.stop_training).grid(row=0, column=7, padx=5)
        ttk.Button(control_frame, text="View Progress", 
                  command=self.show_progress).grid(row=0, column=8, padx=5)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.parent, text="Training Progress", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Progress bars
        ttk.Label(progress_frame, text="Overall Progress:").grid(row=0, column=0, sticky=tk.W)
        self.overall_progress = ttk.Progressbar(progress_frame, length=300)
        self.overall_progress.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5)
        
        ttk.Label(progress_frame, text="Current Epoch:").grid(row=1, column=0, sticky=tk.W)
        self.epoch_progress = ttk.Progressbar(progress_frame, length=300)
        self.epoch_progress.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5)
        
        # Metrics display
        self.metrics_text = tk.Text(progress_frame, height=10, width=50)
        self.metrics_text.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.W+tk.E+tk.N+tk.S)
        progress_frame.grid_columnconfigure(1, weight=1)
        progress_frame.grid_rowconfigure(2, weight=1)
        
        # Visualization frame
        if MATPLOTLIB_AVAILABLE:
            viz_frame = ttk.LabelFrame(self.parent, text="Training Visualization", padding="10")
            viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Matplotlib figure
            self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
            self.canvas = FigureCanvasTkAgg(self.fig, viz_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Initialize plots
            self.loss_history = []
            self.accuracy_history = []
            self.update_plots()
        else:
            # No matplotlib - show message
            viz_frame = ttk.LabelFrame(self.parent, text="Training Visualization", padding="10")
            viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            tk.Label(viz_frame, text="Matplotlib not available. Install with: pip install matplotlib numpy").pack(pady=20)
            self.fig = None
            self.canvas = None
        
    def start_training(self):
        """Start training process"""
        if self.training_active:
            messagebox.showwarning("Training Active", "Training is already running")
            return
            
        self.training_active = True
        threading.Thread(target=self.run_training, daemon=True).start()
        
    def run_training(self):
        """Run the training process"""
        try:
            # Simulate training progress
            total_epochs = int(self.epochs_var.get())
            
            for epoch in range(total_epochs):
                if not self.training_active:
                    break
                    
                # Update progress
                progress = (epoch + 1) / total_epochs
                self.overall_progress['value'] = progress * 100
                self.epoch_progress['value'] = 100  # Reset each epoch
                
                # Simulate metrics
                if np:
                    loss = np.exp(-epoch / 20) + np.random.normal(0, 0.1)
                    accuracy = 1 - loss + np.random.normal(0, 0.05)
                else:
                    loss = 1.0 - (epoch / total_epochs) * 0.5
                    accuracy = 0.5 + (epoch / total_epochs) * 0.4
                
                # Update metrics display
                metrics_text = f"Epoch {epoch+1}/{total_epochs}\n"
                metrics_text += f"Loss: {loss:.4f}\n"
                metrics_text += f"Accuracy: {accuracy:.4f}\n"
                metrics_text += f"Learning Rate: 0.001\n"
                
                self.metrics_text.delete(1.0, tk.END)
                self.metrics_text.insert(1.0, metrics_text)
                
                # Update plots
                if self.fig:
                    self.update_plots(epoch, loss, accuracy)
                
                time.sleep(0.5)  # Simulate training time
                
            if self.training_active:
                messagebox.showinfo("Training Complete", "Model training completed successfully!")
                
        except Exception as e:
            messagebox.showerror("Training Error", f"Training failed: {str(e)}")
        finally:
            self.training_active = False
            
    def stop_training(self):
        """Stop training process"""
        self.training_active = False
        self.overall_progress['value'] = 0
        self.epoch_progress['value'] = 0
        
    def show_progress(self):
        """Show detailed training progress"""
        # This would show detailed training logs and metrics
        messagebox.showinfo("Training Details", 
                           "Detailed training metrics and visualization would appear here.")

    def update_plots(self, epoch=0, loss=1.0, accuracy=0.0):
        """Update training plots"""
        if not MATPLOTLIB_AVAILABLE or not self.fig:
            return
            
        # Simple plot update - in real implementation, this would track actual metrics
        if epoch == 0:
            self.loss_history = [loss]
            self.accuracy_history = [accuracy]
        else:
            self.loss_history.append(loss)
            self.accuracy_history.append(accuracy)
            
        self.ax1.clear()
        self.ax2.clear()
        
        self.ax1.plot(self.loss_history, 'r-', label='Loss')
        self.ax1.set_title('Training Loss')
        self.ax1.set_xlabel('Epoch')
        self.ax1.set_ylabel('Loss')
        self.ax1.legend()
        
        self.ax2.plot(self.accuracy_history, 'g-', label='Accuracy')
        self.ax2.set_title('Training Accuracy')
        self.ax2.set_xlabel('Epoch')
        self.ax2.set_ylabel('Accuracy')
        self.ax2.legend()
        
        self.canvas.draw()

