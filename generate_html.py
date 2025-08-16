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
        'Michael Schwartzbach': 'Michael I. Schwartzbach'
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
    
    return {
        'first_phds': first_phds,
        'top_supervisors': top_supervisors,
        'longest_chains': longest_chains,
        'top_descendants': top_descendants,
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
    <title>daimidata.dk</title>
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
                                <span>Top Vejledere</span>
                            </a>
                        </li>
                        <li :class="{{'is-active': activeTab === 'chains'}}">
                            <a @click="activeTab = 'chains'">
                                <span class="icon"><i class="fas fa-link"></i></span>
                                <span>Længste Kæder</span>
                            </a>
                        </li>
                        <li :class="{{'is-active': activeTab === 'descendants'}}">
                            <a @click="activeTab = 'descendants'">
                                <span class="icon"><i class="fas fa-sitemap"></i></span>
                                <span>Flest Efterkommere</span>
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
                            De 10 største akademiske stamtræer
                        </h2>
                        <div class="content has-text-centered mb-5">
                            <p class="subtitle is-6">
                                Akademiske familier - vejledere med det største samlede antal efterkommere gennem alle generationer.
                                Inkluderer både direkte studerende og deres efterfølgende ph.d.-studerende.
                            </p>
                        </div>
                        <div class="columns is-multiline">
                            <div v-for="(supervisor, index) in topDescendants" :key="index" class="column is-12">
                                <div class="box">
                                    <div class="level">
                                        <div class="level-left">
                                            <div>
                                                <span class="rank-badge">#{{{{ index + 1 }}}}</span>
                                                <span class="title is-4">{{{{ supervisor.name }}}}</span>
                                            </div>
                                        </div>
                                        <div class="level-right">
                                            <div class="has-text-centered">
                                                <p class="heading">Efterkommere</p>
                                                <p class="title is-2 has-text-primary">{{{{ supervisor.descendants }}}}</p>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="descendants-bar" :style="{{width: (supervisor.descendants / topDescendants[0].descendants * 100) + '%'}}"></div>
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
                    <strong>DaimiData.dk er udviklet af <a href>simplesystemer.dk</a> v/Simon Tjell (Daimi-ph.d. #169)</strong> 
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
        
        createApp({{
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