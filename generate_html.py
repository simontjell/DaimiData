#!/usr/bin/env python3
"""
Script to analyze PhD data and generate interactive HTML report.
Includes supervisor chains, hierarchies, and comprehensive statistics.
"""
import json
import re
from collections import defaultdict
from datetime import datetime

def parse_supervisors(supervisor_str):
    """Parse supervisor string to extract individual names"""
    if not supervisor_str:
        return []
    supervisors = re.split(r',\s*|\s+and\s+|\s+&\s+|\s+og\s+', supervisor_str)
    return [s.strip() for s in supervisors if s.strip()]

def normalize_name(name):
    """Normalize names to handle variations"""
    name_map = {
        'Clemens Klokmose': 'Clemens Nylandsted Klokmose',
        'Christian N. S. Pedersen': 'Christian N. Storm Pedersen',
        'Christian Nørgaard Storm Pedersen': 'Christian N. Storm Pedersen',
        'Christian Storm Pedersen': 'Christian N. Storm Pedersen',
        'Jesper Buus': 'Jesper Buus Nielsen',
        'Ivan Damgaard': 'Ivan Bjerre Damgård',
        'Ivan Damgård': 'Ivan Bjerre Damgård',
        'Gerth S. Brodal': 'Gerth Stølting Brodal',
        'Peter Mosses': 'Peter D. Mosses',
        'Michael Schwartzbach': 'Michael I. Schwartzbach',
        'Marianne Graves': 'Marianne Graves Petersen',
        'Jakob Bardram': 'Jakob Eyvind Bardram',
    }
    return name_map.get(name, name)

def find_supervisor_chains(phd_data):
    """Find all supervisor chains where students became supervisors"""
    supervision_graph = defaultdict(list)
    has_supervisor = set()
    student_info = {}
    
    # Build supervision relationships with normalized names
    for entry in phd_data:
        student = normalize_name(entry['name'])
        supervisors = [normalize_name(s) for s in parse_supervisors(entry['supervisors'])]
        
        student_info[student] = {
            'year': entry['year'],
            'title': entry['title'],
            'supervisors': supervisors
        }
        
        for supervisor in supervisors:
            supervision_graph[supervisor].append({
                'name': student,
                'year': entry['year']
            })
            has_supervisor.add(student)
    
    # Find chains using DFS
    chains = []
    phd_students = set(student_info.keys())
    
    def dfs(person, path, years, visited):
        if person in supervision_graph:
            for student in supervision_graph[person]:
                student_name = student['name']
                if student_name in visited or student_name not in phd_students:
                    continue
                    
                new_path = path + [student_name]
                new_years = years + [student['year']]
                new_visited = visited | {student_name}
                
                if len(new_path) >= 2:
                    chains.append({
                        'path': new_path.copy(),
                        'years': new_years.copy(),
                        'length': len(new_path)
                    })
                
                dfs(student_name, new_path, new_years, new_visited)
    
    # Start from root supervisors
    all_supervisors = set(supervision_graph.keys())
    roots = all_supervisors - has_supervisor
    
    for root in roots:
        dfs(root, [root], [None], {root})
    
    # Also from PhD students who became supervisors
    for person in (phd_students & all_supervisors):
        year = student_info[person]['year'] if person in student_info else None
        dfs(person, [person], [year], {person})
    
    # Remove duplicates and sort by length
    unique_chains = []
    seen = set()
    for chain in chains:
        chain_tuple = tuple(chain['path'])
        if chain_tuple not in seen:
            seen.add(chain_tuple)
            unique_chains.append(chain)
    
    return sorted(unique_chains, key=lambda x: x['length'], reverse=True)

def find_all_descendants(person, supervision_graph, visited=None):
    """Recursively find all descendants of a person"""
    if visited is None:
        visited = set()
    
    if person in visited:
        return set()
    
    visited.add(person)
    descendants = set()
    
    if person in supervision_graph:
        for student in supervision_graph[person]:
            student_name = student['name'] if isinstance(student, dict) else student
            if student_name not in visited:
                descendants.add(student_name)
                descendants.update(find_all_descendants(student_name, supervision_graph, visited.copy()))
    
    return descendants

def build_family_tree(root_supervisor, supervision_graph, max_depth=3):
    """Build hierarchical family tree for visualization"""
    
    def build_tree_recursive(person, depth=0):
        if depth >= max_depth or person not in supervision_graph:
            return None
            
        children = []
        for student in supervision_graph[person]:
            student_name = student['name'] if isinstance(student, dict) else student
            student_year = student['year'] if isinstance(student, dict) else None
            
            child_tree = build_tree_recursive(normalize_name(student_name), depth + 1)
            child_node = {
                'name': student_name,
                'year': student_year,
                'children': child_tree['children'] if child_tree else []
            }
            children.append(child_node)
        
        return {
            'name': person,
            'year': None,
            'children': children
        }
    
    return build_tree_recursive(root_supervisor)

def analyze_data(phd_data):
    """Analyze PhD data and generate all required statistics"""
    
    # Build supervision graph
    supervision_graph = defaultdict(list)
    supervisor_counts = defaultdict(int)
    
    for entry in phd_data:
        student = normalize_name(entry['name'])
        supervisors = [normalize_name(s) for s in parse_supervisors(entry['supervisors'])]
        
        for supervisor in supervisors:
            supervision_graph[supervisor].append({
                'name': student,
                'year': entry['year']
            })
            supervisor_counts[supervisor] += 1
    
    # 1. First 10 PhDs
    first_phds = sorted(phd_data, key=lambda x: (x['year'] if x['year'] else 9999, x['name']))[:10]
    
    # 2. Top supervisors
    top_supervisors = sorted(supervisor_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 3. Longest chains - show top 5 by length
    chains = find_supervisor_chains(phd_data)
    longest_chains = sorted(chains, key=lambda x: x['length'], reverse=True)[:5]
    
    # 4. Supervisors with most descendants
    supervisor_descendants = {}
    for supervisor in supervision_graph.keys():
        descendants = find_all_descendants(supervisor, supervision_graph)
        if len(descendants) > 0:
            supervisor_descendants[supervisor] = len(descendants)
    
    top_descendants = sorted(supervisor_descendants.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # 5. Build family trees for top 5 supervisors
    family_trees = []
    for supervisor, descendants_count in top_descendants[:5]:
        tree = build_family_tree(supervisor, supervision_graph, max_depth=3)
        if tree and tree['children']:
            family_trees.append({
                'root': supervisor,
                'descendants': descendants_count,
                'tree': tree
            })
    
    return {
        'first_phds': first_phds,
        'top_supervisors': top_supervisors,
        'longest_chains': longest_chains,
        'top_descendants': top_descendants,
        'family_trees': family_trees,
        'stats': {
            'total_phds': len(phd_data),
            'total_supervisors': len(supervisor_counts),
            'year_span': f"{min(p['year'] for p in phd_data if p['year'])}-{max(p['year'] for p in phd_data if p['year'])}"
        }
    }

def generate_html(analysis_data):
    """Generate HTML report with Vue.js and Bulma CSS"""
    
    html_content = f"""<!DOCTYPE html>
<html lang="da">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>daimi.dk - Ph.d.-statistik for Datalogisk Institut</title>
    
    <!-- Open Graph / LinkedIn meta tags -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://daimi.dk">
    <meta property="og:title" content="daimi.dk - Ph.d.-statistik for Datalogisk Institut">
    <meta property="og:description" content="Interaktiv analyse af {analysis_data['stats']['total_phds']} ph.d.-afhandlinger fra Datalogisk Institut, Aarhus Universitet ({analysis_data['stats']['year_span']}). Udforsk akademiske stamtræer, vejlederkæder og statistikker.">
    <meta property="og:image" content="https://daimi.dk/og-image.png">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="Ph.d.-statistik dashboard for Datalogisk Institut">
    <meta property="og:site_name" content="daimi.dk">
    <meta property="og:locale" content="da_DK">
    
    <!-- Twitter Card meta tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:url" content="https://daimi.dk">
    <meta name="twitter:title" content="daimi.dk - Ph.d.-statistik for Datalogisk Institut">
    <meta name="twitter:description" content="Interaktiv analyse af {analysis_data['stats']['total_phds']} ph.d.-afhandlinger fra Datalogisk Institut, Aarhus Universitet ({analysis_data['stats']['year_span']}).">
    <meta name="twitter:image" content="https://daimi.dk/og-image.png">
    
    <!-- Standard meta tags -->
    <meta name="description" content="Interaktiv analyse af {analysis_data['stats']['total_phds']} ph.d.-afhandlinger fra Datalogisk Institut, Aarhus Universitet ({analysis_data['stats']['year_span']}). Udforsk akademiske stamtræer, vejlederkæder og statistikker.">
    <meta name="keywords" content="ph.d., phd, datalogisk institut, aarhus universitet, akademiske stamtræer, vejlederkæder, computer science">
    <meta name="author" content="Simon Tjell, simplesystemer.dk">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@0.9.4/css/bulma.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.js"></script>
    <style>
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .box {{
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .box:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .chain-person {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            margin: 0.25rem;
            font-weight: 500;
        }}
        .chain-arrow {{
            color: #667eea;
            font-size: 1.5rem;
            margin: 0 0.5rem;
        }}
        .rank-badge {{
            display: inline-block;
            background: #e94560;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: bold;
            margin-right: 0.5rem;
        }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: white;
        }}
        .timeline-item {{
            border-left: 3px solid #667eea;
            padding-left: 1.5rem;
            margin-left: 1rem;
            position: relative;
            padding-bottom: 1.5rem;
        }}
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -8px;
            top: 0;
            width: 13px;
            height: 13px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid white;
        }}
        .fade-enter-active, .fade-leave-active {{
            transition: opacity 0.5s;
        }}
        .fade-enter-from, .fade-leave-to {{
            opacity: 0;
        }}
        .descendants-bar {{
            height: 10px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 5px;
            margin-top: 0.5rem;
            transition: width 0.5s ease;
        }}
        .chain-length-badge {{
            background: #00d1b2;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-weight: bold;
            margin-left: 0.5rem;
        }}
        .tabs {{
            margin-bottom: 2rem;
        }}
        .tabs.is-boxed li.is-active a {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        .tabs.is-boxed a {{
            border: 1px solid #dbdbdb;
            border-radius: 4px 4px 0 0;
            transition: all 0.3s;
        }}
        .tabs.is-boxed a:hover {{
            background: #f5f5f5;
            border-color: #b5b5b5;
        }}
        .tabs.is-boxed li.is-active a:hover {{
            background: #667eea;
            border-color: #667eea;
        }}
        @media screen and (max-width: 1000px) {{
            .tabs.is-centered {{
                justify-content: flex-start;
            }}
            .tabs ul {{
                flex-direction: column;
                width: 100%;
            }}
            .tabs li {{
                width: 100%;
                margin-bottom: 0.5rem;
            }}
            .tabs.is-boxed a {{
                border-radius: 4px;
                justify-content: flex-start;
                padding-left: 1rem;
            }}
        }}
        .family-tree {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }}
        .tree-hierarchy {{
            font-family: 'Courier New', monospace;
            line-height: 1.1;
            font-size: 0.8rem;
        }}
        .tree-root {{
            font-weight: bold;
            color: #667eea;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        }}
        .tree-node {{
            position: relative;
            margin-left: 2rem;
        }}
        .tree-node::before {{
            content: '├── ';
            color: #adb5bd;
            position: absolute;
            left: -1.5rem;
        }}
        .tree-node.is-last::before {{
            content: '└── ';
        }}
        .tree-level-1::before {{
            color: #667eea !important;
            font-weight: bold;
        }}
        .tree-level-2 {{
            color: #6c757d;
        }}
        .tree-level-3 {{
            color: #868e96;
        }}
        .tree-level-4 {{
            color: #9e9e9e;
        }}
        .tree-level-5 {{
            color: #bdbdbd;
        }}
        .person-name {{
            font-weight: 400;
            color: #495057;
        }}
        .person-year {{
            color: #6c757d;
            font-weight: normal;
            margin-left: 0.5rem;
        }}
        .descendants-count {{
            background: #e94560;
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: bold;
            margin-left: 0.5rem;
        }}
    </style>
</head>
<body>
    <div id="app">
        <section class="hero is-medium">
            <div class="hero-body">
                <div class="container has-text-centered">
                    <h1 class="title is-1 has-text-white">
                        ph.d.-statistik
                    </h1>
                    <h2 class="subtitle has-text-white">
                        for Datalogisk Institut ved Aarhus Universitet
                    </h2>
                    <div class="columns is-centered mt-5">
                        <div class="column is-2">
                            <div class="stat-number">{{{{ stats.total_phds }}}}</div>
                            <p class="has-text-white">ph.d.'er ialt</p>
                        </div>
                        <div class="column is-2">
                            <div class="stat-number">{{{{ stats.total_supervisors }}}}</div>
                            <p class="has-text-white">Vejledere</p>
                        </div>
                        <div class="column is-2">
                            <div class="stat-number">{{{{ stats.year_span }}}}</div>
                            <p class="has-text-white">Årrække</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <section class="section">
            <div class="container">
                <!-- Navigation Tabs -->
                <div class="tabs is-centered is-boxed is-large">
                    <ul>
                        <li :class="{{'is-active': activeTab === 'first'}}">
                            <a @click="activeTab = 'first'">
                                <span class="icon"><i class="fas fa-clock-rotate-left"></i></span>
                                <span>Første ph.d.'er</span>
                            </a>
                        </li>
                        <li :class="{{'is-active': activeTab === 'supervisors'}}">
                            <a @click="activeTab = 'supervisors'">
                                <span class="icon"><i class="fas fa-user-tie"></i></span>
                                <span>Flittige vejledere</span>
                            </a>
                        </li>
                        <li :class="{{'is-active': activeTab === 'chains'}}">
                            <a @click="activeTab = 'chains'">
                                <span class="icon"><i class="fas fa-link"></i></span>
                                <span>Lange kæder</span>
                            </a>
                        </li>
                        <li :class="{{'is-active': activeTab === 'descendants'}}">
                            <a @click="activeTab = 'descendants'">
                                <span class="icon"><i class="fas fa-sitemap"></i></span>
                                <span>Stamtræer</span>
                            </a>
                        </li>
                    </ul>
                </div>

                <!-- Content -->
                <transition name="fade" mode="out-in">
                    <!-- First PhDs Tab -->
                    <div v-if="activeTab === 'first'" key="first">
                        <h2 class="title is-3 has-text-centered mb-5">
                            <span class="icon"><i class="fas fa-clock-rotate-left"></i></span>
                            De 10 første ph.d.'er
                        </h2>
                        <div class="columns is-multiline">
                            <div v-for="(phd, index) in firstPhds" :key="index" class="column is-12">
                                <div class="box timeline-item">
                                    <div class="level">
                                        <div class="level-left">
                                            <div>
                                                <span class="rank-badge">#{{{{ index + 1 }}}}</span>
                                                <span class="title is-5">{{{{ phd.name }}}}</span>
                                                <span class="tag is-primary is-light ml-3">{{{{ phd.year }}}}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <p class="mt-2"><strong>Vejleder:</strong> {{{{ phd.supervisors }}}}</p>
                                    <p class="mt-2 has-text-grey">{{{{ phd.title }}}}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Top Supervisors Tab -->
                    <div v-else-if="activeTab === 'supervisors'" key="supervisors">
                        <h2 class="title is-3 has-text-centered mb-5">
                            <span class="icon"><i class="fas fa-user-tie"></i></span>
                            De 10 mest brugte vejledere
                        </h2>
                        <div class="columns is-multiline">
                            <div v-for="(supervisor, index) in topSupervisors" :key="index" class="column is-6">
                                <div class="box">
                                    <div class="level">
                                        <div class="level-left">
                                            <div>
                                                <span class="rank-badge">#{{{{ index + 1 }}}}</span>
                                                <span class="title is-5">{{{{ supervisor.name }}}}</span>
                                            </div>
                                        </div>
                                        <div class="level-right">
                                            <div class="has-text-centered">
                                                <p class="heading">Studerende</p>
                                                <p class="title is-3 has-text-primary">{{{{ supervisor.count }}}}</p>
                                            </div>
                                        </div>
                                    </div>
                                    <progress class="progress is-primary" :value="supervisor.count" :max="topSupervisors[0].count"></progress>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Longest Chains Tab -->
                    <div v-else-if="activeTab === 'chains'" key="chains">
                        <h2 class="title is-3 has-text-centered mb-5">
                            <span class="icon"><i class="fas fa-link"></i></span>
                            De længste vejlederkæder
                        </h2>
                        <div class="content has-text-centered mb-5">
                            <p class="subtitle is-6">
                                Akademiske kæder hvor ph.d.-studerende senere selv blev vejledere og vejledte nye ph.d.'er.
                            </p>
                        </div>
                        <div v-for="(chain, index) in longestChains" :key="index" class="box mb-4">
                            <div class="level mb-3">
                                <div class="level-left">
                                    <span class="rank-badge">#{{{{ index + 1 }}}}</span>
                                    <span class="chain-length-badge">{{{{ chain.path.length }}}} generationer</span>
                                </div>
                            </div>
                            <div class="has-text-centered" style="overflow-x: auto; white-space: nowrap;">
                                <template v-for="(person, i) in chain.path" :key="i">
                                    <span class="chain-person">
                                        {{{{ person }}}}
                                        <span v-if="chain.years[i]" class="has-text-weight-light">
                                            ({{{{ chain.years[i] }}}})
                                        </span>
                                    </span>
                                    <span v-if="i < chain.path.length - 1" class="chain-arrow">→</span>
                                </template>
                            </div>
                        </div>
                    </div>

                    <!-- Most Descendants Tab -->
                    <div v-else-if="activeTab === 'descendants'" key="descendants">
                        <h2 class="title is-3 has-text-centered mb-5">
                            <span class="icon"><i class="fas fa-sitemap"></i></span>
                            Akademiske stamtræer
                        </h2>
                        <div class="content has-text-centered mb-5">
                            <p class="subtitle is-6">
                                Visualisering af de største akademiske familier med deres hierarkiske strukturer.
                                Viser vejleder-studerende relationer gennem generationer.
                            </p>
                        </div>
                        
                        <!-- Family Trees Visualization -->
                        <div v-for="(familyTree, index) in familyTrees" :key="index" class="family-tree">
                            <div class="level mb-4">
                                <div class="level-left">
                                    <div>
                                        <span class="rank-badge">#{{{{ index + 1 }}}}</span>
                                        <span class="title is-4">{{{{ familyTree.root }}}}</span>
                                        <span class="descendants-count">{{{{ familyTree.descendants }}}}</span><span> efterkommere</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Tree Hierarchy -->
                            <div class="tree-hierarchy">
                                <tree-node v-for="(child, index) in familyTree.tree.children" 
                                          :key="child.name" 
                                          :node="child" 
                                          :is-last="index === familyTree.tree.children.length - 1"
                                          :level="1">
                                </tree-node>
                            </div>
                        </div>
                        
                        <!-- Summary Statistics -->
                        <div class="box mt-5">
                            <h3 class="title is-5 mb-4">Top 10 vejledere efter antal efterkommere</h3>
                            <div class="columns is-multiline">
                                <div v-for="(supervisor, index) in topDescendants" :key="index" class="column is-6">
                                    <div class="level">
                                        <div class="level-left">
                                            <span class="rank-badge">#{{{{ index + 1 }}}}</span>
                                            <span class="has-text-weight-semibold">{{{{ supervisor.name }}}}</span>
                                        </div>
                                        <div class="level-right">
                                            <span class="tag is-primary">{{{{ supervisor.descendants }}}} efterkommere</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </transition>
            </div>
        </section>

        <footer class="footer">
            <div class="content has-text-centered" id="about">
                <p>
                    <strong>daimi.dk er udviklet af <a href>simplesystemer.dk</a> v/Simon Tjell (Daimi-ph.d. #169)</strong> 
                    <br>
                    på baggrund af <a href="https://cs.au.dk/education/phd/phds-produced/">data</a> fra Datalogisk Institut, Aarhus Universitet
                    <br>
                    Genereret: {{{{ generatedDate }}}}
                </p>
            </div>
        </footer>
    </div>

    <script>
        const {{ createApp }} = Vue;
        
        const TreeNode = {{
            name: 'TreeNode',
            props: ['node', 'isLast', 'level'],
            template: `
                <div class="tree-node" :class="['tree-level-' + level, {{ 'is-last': isLast }}]">
                    <span class="person-name">{{{{ node.name }}}}</span>
                    <span v-if="node.year" class="person-year">({{{{ node.year }}}})</span>
                    <div v-if="node.children && node.children.length > 0" class="tree-children">
                        <tree-node v-for="(child, index) in node.children" 
                                  :key="child.name" 
                                  :node="child" 
                                  :is-last="index === node.children.length - 1"
                                  :level="level + 1">
                        </tree-node>
                    </div>
                </div>
            `
        }};
        
        createApp({{
            components: {{
                TreeNode
            }},
            data() {{
                return {{
                    activeTab: 'first',
                    stats: {json.dumps(analysis_data['stats'])},
                    firstPhds: {json.dumps([{
                        'name': p['name'],
                        'year': p['year'],
                        'title': p['title'],
                        'supervisors': p['supervisors']
                    } for p in analysis_data['first_phds']])},
                    topSupervisors: {json.dumps([{
                        'name': name,
                        'count': count
                    } for name, count in analysis_data['top_supervisors']])},
                    longestChains: {json.dumps(analysis_data['longest_chains'])},
                    topDescendants: {json.dumps([{
                        'name': name,
                        'descendants': count
                    } for name, count in analysis_data['top_descendants']])},
                    familyTrees: {json.dumps(analysis_data['family_trees'])},
                    generatedDate: '{datetime.now().strftime('%d-%m-%Y %H:%M')}'
                }}
            }}
        }}).mount('#app');
    </script>
</body>
</html>"""
    
    return html_content

def main():
    """Main function to generate HTML report"""
    try:
        # Load PhD data
        with open('data/phd_data.json', 'r', encoding='utf-8') as f:
            phd_data = json.load(f)
        
        print(f"Analyzing {len(phd_data)} PhD entries...")
        
        # Analyze data
        analysis_data = analyze_data(phd_data)
        
        # Generate HTML
        html_content = generate_html(analysis_data)
        
        # Save to docs directory for GitHub Pages
        output_file = "docs/index.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML rapport genereret: {output_file}")
        print(f"- {len(analysis_data['first_phds'])} første PhD'er")
        print(f"- {len(analysis_data['top_supervisors'])} top vejledere") 
        print(f"- {len(analysis_data['longest_chains'])} længste kæder")
        print(f"- {len(analysis_data['top_descendants'])} vejledere med flest efterkommere")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
