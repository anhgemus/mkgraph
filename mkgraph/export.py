"""Export knowledge graph to various formats."""
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from mkgraph.processor import Entity


def entities_to_dict(entities: list[Entity]) -> dict:
    """Convert entities to dictionary format."""
    return {
        "entities": [
            {
                "name": e.name,
                "type": e.entity_type,
                "description": e.description,
                "sources": e.sources,
            }
            for e in entities
        ]
    }


def export_to_json(entities: list[Entity], output_path: Path) -> None:
    """Export entities to JSON format."""
    data = entities_to_dict(entities)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)


def export_to_graphml(entities: list[Entity], output_path: Path) -> None:
    """Export entities to GraphML format."""
    # Create GraphML root
    root = ET.Element("graphml")
    root.set("xmlns", "http://graphml.graphdrawing.org/xmlns")

    # Define node attributes
    key_id = 0
    for attr_name, attr_type in [("label", "string"), ("type", "string"), ("description", "string")]:
        key = ET.SubElement(root, "key")
        key.set("id", str(key_id))
        key.set("for", "node")
        key.set("attr.name", attr_name)
        key.set("attr.type", attr_type)
        key_id += 1

    # Define edge attributes
    source_key = ET.SubElement(root, "key")
    source_key.set("id", str(key_id))
    source_key.set("for", "edge")
    source_key.set("attr.name", "source")
    source_key.set("attr.type", "string")

    # Graph element
    graph = ET.SubElement(root, "graph")
    graph.set("id", "G")
    graph.set("edgedefault", "undirected")

    # Track node IDs for relationships
    node_ids: dict[str, str] = {}

    # Add nodes
    for i, entity in enumerate(entities):
        node = ET.SubElement(graph, "node")
        node_id = f"n{i}"
        node.set("id", node_id)
        node_ids[f"{entity.name}:{entity.entity_type}"] = node_id

        # Add node data
        data_label = ET.SubElement(node, "data")
        data_label.set("key", "0")
        data_label.text = entity.name

        data_type = ET.SubElement(node, "data")
        data_type.set("key", "1")
        data_type.text = entity.entity_type

        data_desc = ET.SubElement(node, "data")
        data_desc.set("key", "2")
        data_desc.text = entity.description[:500] if entity.description else ""

    # Add edges based on shared sources
    for i, entity1 in enumerate(entities):
        for j, entity2 in enumerate(entities):
            if i >= j:
                continue
            # Check if entities share sources
            shared_sources = set(entity1.sources) & set(entity2.sources)
            if shared_sources:
                edge = ET.SubElement(graph, "edge")
                edge.set("id", f"e{i}-{j}")
                edge.set("source", node_ids[f"{entity1.name}:{entity1.entity_type}"])
                edge.set("target", node_ids[f"{entity2.name}:{entity2.entity_type}"])

                data_source = ET.SubElement(edge, "data")
                data_source.set("key", str(key_id))
                data_source.text = ", ".join(shared_sources)

    # Write to file
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def export_to_html(entities: list[Entity], output_path: Path) -> None:
    """Export entities to interactive HTML visualization."""
    # Group entities by type
    people = [e for e in entities if e.entity_type == "person"]
    orgs = [e for e in entities if e.entity_type == "organization"]
    topics = [e for e in entities if e.entity_type == "topic"]

    # Build nodes and links for visualization
    nodes = []
    links = []
    node_id_map: dict[str, int] = {}

    for i, entity in enumerate(entities):
        node_id_map[f"{entity.name}:{entity.entity_type}"] = i
        nodes.append({
            "id": i,
            "name": entity.name,
            "type": entity.entity_type,
            "description": entity.description[:200] if entity.description else "",
            "sources": entity.sources,
        })

    # Create links from shared sources
    for i, entity1 in enumerate(entities):
        for j, entity2 in enumerate(entities):
            if i >= j:
                continue
            shared_sources = set(entity1.sources) & set(entity2.sources)
            if shared_sources:
                links.append({
                    "source": i,
                    "target": j,
                    "label": ", ".join([Path(s).stem for s in shared_sources]),
                })

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Knowledge Graph</title>
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .stats {{ margin-bottom: 20px; color: #666; }}
        #graph {{ width: 100%; height: 600px; border: 1px solid #ddd; background: white; border-radius: 8px; }}
        .node circle {{ stroke: #fff; stroke-width: 2px; cursor: pointer; }}
        .node text {{ font-size: 12px; }}
        .link {{ stroke: #999; stroke-opacity: 0.6; }}
        .legend {{ position: absolute; top: 20px; right: 20px; background: white; padding: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .legend-item {{ display: flex; align-items: center; margin: 5px 0; }}
        .legend-color {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        .tooltip {{ position: absolute; background: white; padding: 10px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); max-width: 300px; }}
    </style>
</head>
<body>
    <h1>Knowledge Graph</h1>
    <div class="stats">
        <strong>{len(people)}</strong> people ·
        <strong>{len(orgs)}</strong> organizations ·
        <strong>{len(topics)}</strong> topics ·
        <strong>{len(links)}</strong> connections
    </div>
    <div id="graph"></div>

    <script type="text/javascript">
        const nodes = {json.dumps(nodes)};
        const links = {json.dumps(links)};

        const colors = {{ person: "#4fc3f7", organization: "#81c784", topic: "#ffb74d" }};

        const width = document.getElementById('graph').clientWidth;
        const height = 600;

        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links).id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));

        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .join('line')
            .attr('class', 'link')
            .attr('stroke-width', 2);

        const node = svg.append('g')
            .selectAll('g')
            .data(nodes)
            .join('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        node.append('circle')
            .attr('r', 15)
            .attr('fill', d => colors[d.type]);

        node.append('text')
            .attr('dx', 18)
            .attr('dy', 4)
            .text(d => d.name);

        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}

        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}

        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
    </script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)


def load_entities_from_directory(directory: Path) -> list[Entity]:
    """Load entities from a knowledge graph directory."""
    entities = []

    for entity_type in ["People", "Organizations", "Topics"]:
        type_dir = directory / entity_type
        if not type_dir.exists():
            continue

        for md_file in type_dir.glob("*.md"):
            # Parse frontmatter
            with open(md_file) as f:
                content = f.read()

            # Extract name from filename
            name = md_file.stem

            # Determine entity type
            if entity_type == "people":
                entity_type_str = "person"
            elif entity_type == "organizations":
                entity_type_str = "organization"
            else:
                entity_type_str = "topic"

            # Extract description (first paragraph after frontmatter)
            description = ""
            lines = content.split("\n")
            in_frontmatter = False
            for line in lines:
                if line.strip() == "---":
                    in_frontmatter = not in_frontmatter
                elif not in_frontmatter and line.strip() and not line.startswith("#"):
                    description = line.strip()
                    break

            # Extract sources
            sources = []
            for line in lines:
                if line.strip().startswith("- "):
                    sources.append(line.strip()[2:])

            entities.append(Entity(
                name=name,
                entity_type=entity_type_str,
                description=description,
                sources=sources,
            ))

    return entities
