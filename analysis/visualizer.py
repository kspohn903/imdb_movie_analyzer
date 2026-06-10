import matplotlib.pyplot as plt
import seaborn as sns

class EmpiricalVisualizer:
    @staticmethod
    def save_velocity_plot(lifecycle_data, label, output_dir="./graphics"):
        plt.figure(figsize=(10, 6))
        years = [x.start_year for x in lifecycle_data]
        spans = [x.production_span for x in lifecycle_data]
        
        sns.lineplot(x=years, y=spans, marker="o")
        plt.title(f"Production Cadence Analysis: {label}")
        plt.savefig(f"{output_dir}/{label}_velocity_profile.png")
        plt.close()
