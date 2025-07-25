#!/usr/bin/env python3
"""
Visual Dependency Graph Generator
Generates before/after dependency graphs to show architectural impact of changes.
"""

import os
import ast
import json
import re
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
import subprocess
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class DependencyNode:
    """Represents a node in the dependency graph"""
    name: str
    file_path: str
    type: str  # 'file', 'class', 'function', 'component'
    dependencies: Set[str]
    dependents: Set[str]
    lines_of_code: int = 0
    complexity_score: float = 0.0

@dataclass
class DependencyChange:
    """Represents a change in dependencies"""
    node_name: str
    change_type: str  # 'added', 'removed', 'modified'
    before_deps: Set[str]
    after_deps: Set[str]
    impact_score: float = 0.0

class DependencyGraphGenerator:
    """Generates visual dependency graphs from code changes"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.before_graph: Dict[str, DependencyNode] = {}
        self.after_graph: Dict[str, DependencyNode] = {}
        self.changes: List[DependencyChange] = []
        
    def analyze_python_file(self, file_path: Path) -> DependencyNode:
        """Analyze a Python file for dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            dependencies = set()
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.add(node.module)
                        
            # Count lines and estimate complexity
            lines = len([line for line in content.split('\n') if line.strip()])
            complexity = self._calculate_complexity(tree)
            
            return DependencyNode(
                name=file_path.stem,
                file_path=str(file_path),
                type='file',
                dependencies=dependencies,
                dependents=set(),
                lines_of_code=lines,
                complexity_score=complexity
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return DependencyNode(
                name=file_path.stem,
                file_path=str(file_path),
                type='file',
                dependencies=set(),
                dependents=set()
            )
    
    def analyze_typescript_file(self, file_path: Path) -> DependencyNode:
        """Analyze a TypeScript/JavaScript file for dependencies"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            dependencies = set()
            
            # Extract ES6 imports
            import_pattern = r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"
            imports = re.findall(import_pattern, content)
            dependencies.update(imports)
            
            # Extract require statements
            require_pattern = r"require\(['\"]([^'\"]+)['\"]\)"
            requires = re.findall(require_pattern, content)
            dependencies.update(requires)
            
            # Count lines
            lines = len([line for line in content.split('\n') if line.strip()])
            
            return DependencyNode(
                name=file_path.stem,
                file_path=str(file_path),
                type='file',
                dependencies=dependencies,
                dependents=set(),
                lines_of_code=lines
            )
            
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return DependencyNode(
                name=file_path.stem,
                file_path=str(file_path),
                type='file',
                dependencies=set(),
                dependents=set()
            )
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate McCabe complexity for Python AST"""
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
                
        return complexity
    
    def build_graph_from_commit(self, commit_hash: str) -> Dict[str, DependencyNode]:
        """Build dependency graph from a specific commit"""
        graph = {}
        
        # Get list of files from commit
        try:
            result = subprocess.run(
                ['git', 'ls-tree', '-r', '--name-only', commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"Error getting files from commit {commit_hash}")
                return graph
                
            files = result.stdout.strip().split('\n')
            
            for file_path in files:
                if not file_path:
                    continue
                    
                full_path = self.repo_path / file_path
                
                if file_path.endswith('.py'):
                    # Get file content from commit
                    content_result = subprocess.run(
                        ['git', 'show', f'{commit_hash}:{file_path}'],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if content_result.returncode == 0:
                        # Write temporary file for analysis
                        temp_file = Path(f"/tmp/{Path(file_path).name}")
                        with open(temp_file, 'w') as f:
                            f.write(content_result.stdout)
                        
                        node = self.analyze_python_file(temp_file)
                        node.file_path = file_path
                        graph[file_path] = node
                        
                        # Clean up
                        temp_file.unlink(missing_ok=True)
                        
                elif file_path.endswith(('.ts', '.tsx', '.js', '.jsx')):
                    # Similar process for TypeScript files
                    content_result = subprocess.run(
                        ['git', 'show', f'{commit_hash}:{file_path}'],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True
                    )
                    
                    if content_result.returncode == 0:
                        temp_file = Path(f"/tmp/{Path(file_path).name}")
                        with open(temp_file, 'w') as f:
                            f.write(content_result.stdout)
                        
                        node = self.analyze_typescript_file(temp_file)
                        node.file_path = file_path
                        graph[file_path] = node
                        
                        temp_file.unlink(missing_ok=True)
                        
        except Exception as e:
            print(f"Error building graph from commit {commit_hash}: {e}")
            
        return graph
    
    def compare_graphs(self, before_commit: str, after_commit: str) -> List[DependencyChange]:
        """Compare dependency graphs between two commits"""
        self.before_graph = self.build_graph_from_commit(before_commit)
        self.after_graph = self.build_graph_from_commit(after_commit)
        
        changes = []
        
        # Find all unique file paths
        all_files = set(self.before_graph.keys()) | set(self.after_graph.keys())
        
        for file_path in all_files:
            before_node = self.before_graph.get(file_path)
            after_node = self.after_graph.get(file_path)
            
            if before_node and not after_node:
                # File was removed
                changes.append(DependencyChange(
                    node_name=file_path,
                    change_type='removed',
                    before_deps=before_node.dependencies,
                    after_deps=set(),
                    impact_score=len(before_node.dependents)
                ))
                
            elif not before_node and after_node:
                # File was added
                changes.append(DependencyChange(
                    node_name=file_path,
                    change_type='added',
                    before_deps=set(),
                    after_deps=after_node.dependencies,
                    impact_score=len(after_node.dependencies)
                ))
                
            elif before_node and after_node:
                # File was modified - check if dependencies changed
                if before_node.dependencies != after_node.dependencies:
                    impact_score = (
                        len(after_node.dependencies - before_node.dependencies) +
                        len(before_node.dependencies - after_node.dependencies)
                    )
                    
                    changes.append(DependencyChange(
                        node_name=file_path,
                        change_type='modified',
                        before_deps=before_node.dependencies,
                        after_deps=after_node.dependencies,
                        impact_score=impact_score
                    ))
        
        self.changes = changes
        return changes
    
    def generate_graphviz_dot(self, output_file: str, include_changes: bool = True):
        """Generate Graphviz DOT file for visualization"""
        dot_content = ["digraph DependencyGraph {"]
        dot_content.append("    rankdir=LR;")
        dot_content.append("    node [shape=box, style=rounded];")
        
        # Add nodes
        for file_path, node in self.after_graph.items():
            color = "lightblue"
            if include_changes:
                # Color nodes based on changes
                for change in self.changes:
                    if change.node_name == file_path:
                        if change.change_type == 'added':
                            color = "lightgreen"
                        elif change.change_type == 'removed':
                            color = "lightcoral"
                        elif change.change_type == 'modified':
                            color = "lightyellow"
                        break
            
            dot_content.append(
                f'    "{file_path}" [label="{Path(file_path).name}\\n{node.lines_of_code} LOC", '
                f'fillcolor="{color}", style=filled];'
            )
        
        # Add edges (dependencies)
        for file_path, node in self.after_graph.items():
            for dep in node.dependencies:
                # Only show internal dependencies
                dep_file = None
                for other_file in self.after_graph.keys():
                    if Path(other_file).stem == dep or dep in other_file:
                        dep_file = other_file
                        break
                
                if dep_file:
                    dot_content.append(f'    "{file_path}" -> "{dep_file}";')
        
        dot_content.append("}")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(dot_content))
    
    def generate_html_visualization(self, output_file: str):
        """Generate interactive HTML visualization using D3.js"""
        # Prepare data for D3.js
        nodes = []
        links = []
        
        for file_path, node in self.after_graph.items():
            change_type = "unchanged"
            for change in self.changes:
                if change.node_name == file_path:
                    change_type = change.change_type
                    break
            
            nodes.append({
                "id": file_path,
                "name": Path(file_path).name,
                "group": change_type,
                "size": node.lines_of_code,
                "complexity": node.complexity_score
            })
            
            for dep in node.dependencies:
                # Find corresponding file
                for other_file in self.after_graph.keys():
                    if Path(other_file).stem == dep or dep in other_file:
                        links.append({
                            "source": file_path,
                            "target": other_file,
                            "value": 1
                        })
                        break
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Dependency Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .node {{ stroke: #fff; stroke-width: 1.5px; }}
        .link {{ stroke: #999; stroke-opacity: 0.6; }}
        .tooltip {{ position: absolute; text-align: center; padding: 8px; 
                   background: rgba(0,0,0,0.8); color: white; border-radius: 4px; 
                   pointer-events: none; font-size: 12px; }}
        .legend {{ position: absolute; top: 20px; right: 20px; }}
        .legend-item {{ margin: 5px 0; }}
        .legend-color {{ width: 15px; height: 15px; display: inline-block; margin-right: 8px; }}
    </style>
</head>
<body>
    <h1>Dependency Graph Changes</h1>
    <div class="legend">
        <div class="legend-item"><span class="legend-color" style="background: #4CAF50;"></span>Added</div>
        <div class="legend-item"><span class="legend-color" style="background: #FFC107;"></span>Modified</div>
        <div class="legend-item"><span class="legend-color" style="background: #F44336;"></span>Removed</div>
        <div class="legend-item"><span class="legend-color" style="background: #2196F3;"></span>Unchanged</div>
    </div>
    <svg width="1200" height="800"></svg>
    
    <script>
        const nodes = {json.dumps(nodes)};
        const links = {json.dumps(links)};
        
        const svg = d3.select("svg");
        const width = +svg.attr("width");
        const height = +svg.attr("height");
        
        const color = d3.scaleOrdinal()
            .domain(["added", "modified", "removed", "unchanged"])
            .range(["#4CAF50", "#FFC107", "#F44336", "#2196F3"]);
        
        const simulation = d3.forceSimulation()
            .force("link", d3.forceLink().id(d => d.id))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));
        
        const link = svg.append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("class", "link");
        
        const node = svg.append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("class", "node")
            .attr("r", d => Math.max(5, Math.sqrt(d.size) / 2))
            .attr("fill", d => color(d.group))
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        const tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);
        
        node.on("mouseover", function(event, d) {{
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(`${{d.name}}<br/>LOC: ${{d.size}}<br/>Type: ${{d.group}}`)
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", function(d) {{
            tooltip.transition().duration(500).style("opacity", 0);
        }});
        
        simulation
            .nodes(nodes)
            .on("tick", ticked);
        
        simulation.force("link")
            .links(links);
        
        function ticked() {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
        }}
        
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_template)

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate dependency graph visualizations')
    parser.add_argument('--repo', required=True, help='Repository path')
    parser.add_argument('--before', required=True, help='Before commit hash')
    parser.add_argument('--after', required=True, help='After commit hash')
    parser.add_argument('--output-dot', help='Output DOT file path')
    parser.add_argument('--output-html', help='Output HTML file path')
    parser.add_argument('--pr-output', action='store_true',
                       help='Generate output for PR comment integration')
    
    args = parser.parse_args()
    
    generator = DependencyGraphGenerator(args.repo)
    changes = generator.compare_graphs(args.before, args.after)
    
    print(f"Found {len(changes)} dependency changes:")
    for change in changes:
        print(f"  {change.change_type}: {change.node_name} (impact: {change.impact_score})")
    
    # Prepare results for PR integration
    pr_result = {
        'changes': [
            {
                'file_path': change.node_name,
                'file_name': Path(change.node_name).name,
                'change_type': change.change_type,
                'impact_score': change.impact_score,
                'dependencies_before': list(change.before_deps),
                'dependencies_after': list(change.after_deps)
            }
            for change in changes
        ],
        'total_files_analyzed': len(generator.before_graph) + len(generator.after_graph),
        'graph_generated': False,
        'circular_dependencies': [],  # Would need additional analysis
        'high_impact_changes': [
            {
                'file_path': change.node_name,
                'file_name': Path(change.node_name).name,
                'change_type': change.change_type,
                'impact_score': change.impact_score
            }
            for change in changes if change.impact_score > 2
        ],
        'graph_files': {
            'png': None,
            'html': None,
            'ascii': None
        }
    }
    
    # Generate visual dependency graphs using the visualizer
    try:
        from dependency_graph_visualizer import generate_dependency_graph_image, generate_interactive_graph
        
        # Convert our graph to simple dependency format
        simple_deps = {}
        for file_path, node in generator.after_graph.items():
            simple_deps[file_path] = list(node.dependencies)
        
        # Generate PNG image
        png_file = generate_dependency_graph_image(simple_deps, '.')
        if png_file:
            pr_result['graph_files']['png'] = png_file
            pr_result['graph_generated'] = True
        
        # Generate interactive HTML
        html_file = generate_interactive_graph(simple_deps, '.')
        if html_file:
            pr_result['graph_files']['html'] = html_file
            pr_result['graph_generated'] = True
            
    except ImportError:
        print("Visual graph generator not available, using basic output")
    
    if args.output_dot:
        generator.generate_graphviz_dot(args.output_dot)
        print(f"Generated DOT file: {args.output_dot}")
    
    if args.output_html:
        generator.generate_html_visualization(args.output_html)
        pr_result['graph_files']['html'] = args.output_html
        pr_result['graph_generated'] = True
        print(f"Generated HTML visualization: {args.output_html}")
    
    # Always generate PR integration file if in GitHub Actions
    if args.pr_output or os.getenv('GITHUB_ACTIONS'):
        pr_output_file = 'dependency-graph-results.json'
        with open(pr_output_file, 'w') as f:
            json.dump(pr_result, f, indent=2)
        print(f"PR integration results written to {pr_output_file}")

if __name__ == "__main__":
    main()
