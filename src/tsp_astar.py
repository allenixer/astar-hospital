import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import heapq
from matplotlib.widgets import Button
import math

class HospitalNavigator:
    def __init__(self):
        # Hospital floor plan (20x15 grid)
        # 0 = walkable, 1 = wall, 2 = room, 3 = special areas
        self.grid = np.array([
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,0,0,0,1,2,2,2,1,0,0,0,0,0,1,2,2,2,2,1],
            [1,0,0,0,1,2,2,2,1,0,0,0,0,0,1,2,2,2,2,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,2,2,1,1,1,0,0,0,0,0,0,1,1,1,0,0,0,0,1],
            [1,2,2,1,3,3,0,0,0,0,0,0,1,2,2,0,0,0,0,1],
            [1,2,2,1,3,3,0,0,0,0,0,0,1,2,2,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0,1,1,1,1],
            [1,2,2,2,1,0,0,0,1,3,3,0,0,0,2,2,1,2,2,1],
            [1,2,2,2,1,0,0,0,1,3,3,0,0,0,2,2,1,2,2,1],
            [1,2,2,2,1,0,0,0,1,1,1,0,0,0,2,2,1,2,2,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        ])
        
        # Room labels for reference
        self.room_labels = {
            (1, 5): "Ward A", (1, 16): "Ward B", (4, 1): "Lab", (4, 4): "OR",
            (5, 13): "ICU", (9, 1): "Emergency", (9, 9): "Radiology", 
            (9, 15): "Pharmacy", (9, 17): "Reception"
        }
        
        self.rows, self.cols = self.grid.shape
        self.start = None
        self.goal = None
        self.path = []
        self.visited = set()
        
        self.setup_plot()
        
    def setup_plot(self):
        """Initialize the matplotlib interface"""
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        plt.subplots_adjust(bottom=0.15)
        
        # Create buttons
        ax_clear = plt.axes([0.1, 0.05, 0.1, 0.04])
        ax_find = plt.axes([0.25, 0.05, 0.15, 0.04])
        ax_reset = plt.axes([0.45, 0.05, 0.1, 0.04])
        
        self.btn_clear = Button(ax_clear, 'Clear')
        self.btn_find = Button(ax_find, 'Find Path')
        self.btn_reset = Button(ax_reset, 'Reset')
        
        self.btn_clear.on_clicked(self.clear_selection)
        self.btn_find.on_clicked(self.find_path)
        self.btn_reset.on_clicked(self.reset_all)
        
        # Connect click event
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        self.draw_hospital()
        
    def draw_hospital(self):
        """Draw the hospital floor plan"""
        self.ax.clear()
        
        # Color mapping
        colors = {0: 'white', 1: 'black', 2: 'lightblue', 3: 'lightgreen'}
        
        for i in range(self.rows):
            for j in range(self.cols):
                color = colors[self.grid[i, j]]
                rect = patches.Rectangle((j, self.rows-1-i), 1, 1, 
                                       linewidth=0.5, edgecolor='gray', 
                                       facecolor=color)
                self.ax.add_patch(rect)
        
        # Add room labels
        for (i, j), label in self.room_labels.items():
            self.ax.text(j+0.5, self.rows-1-i+0.5, label, 
                        ha='center', va='center', fontsize=8, 
                        bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Draw start and goal points
        if self.start:
            circle = patches.Circle((self.start[1]+0.5, self.rows-1-self.start[0]+0.5), 
                                   0.3, color='green', zorder=5)
            self.ax.add_patch(circle)
            self.ax.text(self.start[1]+0.5, self.rows-1-self.start[0]+0.1, 'START', 
                        ha='center', va='center', fontweight='bold', color='white')
            
        if self.goal:
            circle = patches.Circle((self.goal[1]+0.5, self.rows-1-self.goal[0]+0.5), 
                                   0.3, color='red', zorder=5)
            self.ax.add_patch(circle)
            self.ax.text(self.goal[1]+0.5, self.rows-1-self.goal[0]+0.1, 'GOAL', 
                        ha='center', va='center', fontweight='bold', color='white')
        
        # Draw visited cells (exploration)
        for (i, j) in self.visited:
            if (i, j) != self.start and (i, j) != self.goal:
                circle = patches.Circle((j+0.5, self.rows-1-i+0.5), 
                                       0.1, color='orange', alpha=0.6, zorder=3)
                self.ax.add_patch(circle)
        
        # Draw path
        if self.path:
            for i in range(len(self.path)-1):
                curr = self.path[i]
                next_pos = self.path[i+1]
                self.ax.plot([curr[1]+0.5, next_pos[1]+0.5], 
                           [self.rows-1-curr[0]+0.5, self.rows-1-next_pos[0]+0.5], 
                           'r-', linewidth=4, alpha=0.8, zorder=4)
        
        self.ax.set_xlim(0, self.cols)
        self.ax.set_ylim(0, self.rows)
        self.ax.set_aspect('equal')
        self.ax.set_title('Hospital Indoor Navigation - Click to set Start (green) and Goal (red)')
        
        # Add legend
        legend_elements = [
            patches.Patch(color='white', label='Walkable'),
            patches.Patch(color='black', label='Wall'),
            patches.Patch(color='lightblue', label='Patient Rooms'),
            patches.Patch(color='lightgreen', label='Special Areas'),
            patches.Patch(color='orange', label='Explored'),
            patches.Patch(color='red', label='Optimal Path')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        plt.draw()
    
    def on_click(self, event):
        """Handle mouse clicks to set start and goal"""
        if event.inaxes != self.ax:
            return
            
        col = int(event.xdata)
        row = self.rows - 1 - int(event.ydata)
        
        # Check if clicked position is valid (walkable)
        if (0 <= row < self.rows and 0 <= col < self.cols and 
            self.grid[row, col] in [0, 2, 3]):
            
            if self.start is None:
                self.start = (row, col)
                print(f"Start set at: Row {row}, Col {col}")
            elif self.goal is None:
                self.goal = (row, col)
                print(f"Goal set at: Row {row}, Col {col}")
            else:
                # Reset and set new start
                self.start = (row, col)
                self.goal = None
                self.path = []
                self.visited = set()
                print(f"New start set at: Row {row}, Col {col}")
            
            self.draw_hospital()
    
    def heuristic(self, a, b):
        """Calculate Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(self, pos):
        """Get valid neighboring positions"""
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
        
        for dx, dy in directions:
            new_row, new_col = pos[0] + dx, pos[1] + dy
            
            if (0 <= new_row < self.rows and 0 <= new_col < self.cols and 
                self.grid[new_row, new_col] != 1):  # Not a wall
                neighbors.append((new_row, new_col))
        
        return neighbors
    
    def astar_search(self):
        """Implement A* pathfinding algorithm"""
        if not self.start or not self.goal:
            print("Please set both start and goal points!")
            return []
        
        open_set = []
        heapq.heappush(open_set, (0, self.start))
        
        came_from = {}
        g_score = {self.start: 0}
        f_score = {self.start: self.heuristic(self.start, self.goal)}
        
        self.visited = set()
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            self.visited.add(current)
            
            if current == self.goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(self.start)
                return path[::-1]
            
            for neighbor in self.get_neighbors(current):
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, self.goal)
                    
                    if not any(neighbor == item[1] for item in open_set):
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found
    
    def find_path(self, event):
        """Find and display the optimal path"""
        self.path = self.astar_search()
        if self.path:
            print(f"Path found! Length: {len(self.path)} steps")
            print(f"Path coordinates: {self.path}")
        else:
            print("No path found!")
        self.draw_hospital()
    
    def clear_selection(self, event):
        """Clear current selection"""
        self.path = []
        self.visited = set()
        self.draw_hospital()
    
    def reset_all(self, event):
        """Reset everything"""
        self.start = None
        self.goal = None
        self.path = []
        self.visited = set()
        self.draw_hospital()
        print("All selections cleared!")

# Run the hospital navigation system
if __name__ == "__main__":
    navigator = HospitalNavigator()
    plt.show()
    
    # Instructions for user
    print("\n=== Hospital Indoor Navigation System ===")
    print("Instructions:")
    print("1. Click on any walkable area (white, blue, or green) to set START point")
    print("2. Click again to set GOAL point")
    print("3. Click 'Find Path' to calculate optimal route")
    print("4. Use 'Clear' to remove path visualization")
    print("5. Use 'Reset' to start over")
    print("\nColor Legend:")
    print("- White: Hallways/Walkable areas")
    print("- Black: Walls (non-walkable)")
    print("- Light Blue: Patient rooms")
    print("- Light Green: Special areas (OR, Radiology, etc.)")
    print("- Orange dots: Areas explored by A* algorithm")
    print("- Red line: Optimal path found")