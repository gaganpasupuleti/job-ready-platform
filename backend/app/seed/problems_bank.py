"""Original coding problem bank for Build 3.1 seed (~20 problems)."""

from app.models.enums import Difficulty

ALL_LANG_IDS = [71, 62, 54, 63]


def _starters(python: str, java: str, cpp: str, js: str) -> dict[str, str]:
    return {"71": python, "62": java, "54": cpp, "63": js}


ECHO_STARTER = _starters(
    python="import sys\nprint(sys.stdin.read().strip())\n",
    java="import java.util.Scanner;\npublic class Main {\n  public static void main(String[] args) {\n    Scanner sc = new Scanner(System.in);\n    System.out.println(sc.hasNextLine() ? sc.nextLine() : \"\");\n  }\n}\n",
    cpp="#include <iostream>\n#include <string>\nusing namespace std;\nint main() { string s; getline(cin, s); cout << s; return 0; }\n",
    js="const fs=require('fs');\nconsole.log(fs.readFileSync(0,'utf8').trim());\n",
)

ADD_STARTER = _starters(
    python="a, b = map(int, input().split())\nprint(a + b)\n",
    java="import java.util.Scanner;\npublic class Main {\n  public static void main(String[] args) {\n    Scanner sc = new Scanner(System.in);\n    System.out.println(sc.nextInt() + sc.nextInt());\n  }\n}\n",
    cpp="#include <iostream>\nusing namespace std;\nint main() { int a,b; cin>>a>>b; cout<<a+b; return 0; }\n",
    js="const fs=require('fs');\nconst [a,b]=fs.readFileSync(0,'utf8').trim().split(/\\s+/).map(Number);\nconsole.log(a+b);\n",
)

REVERSE_STARTER = _starters(
    python="s = input().strip()\nprint(s[::-1])\n",
    java="import java.util.Scanner;\npublic class Main {\n  public static void main(String[] args) {\n    Scanner sc = new Scanner(System.in);\n    String s = sc.nextLine();\n    System.out.println(new StringBuilder(s).reverse());\n  }\n}\n",
    cpp="#include <iostream>\n#include <algorithm>\n#include <string>\nusing namespace std;\nint main() { string s; getline(cin,s); reverse(s.begin(),s.end()); cout<<s; return 0; }\n",
    js="const fs=require('fs');\nconst s=fs.readFileSync(0,'utf8').trim();\nconsole.log(s.split('').reverse().join(''));\n",
)

TWO_SUM_STARTER = _starters(
    python='''def two_sum(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
import sys
lines = sys.stdin.read().strip().split("\\n")
nums = eval(lines[0])
target = int(lines[1])
print(two_sum(nums, target))
''',
    java='''import java.util.*;
public class Main {
  public static void main(String[] args) {
    Scanner sc = new Scanner(System.in);
    String[] parts = sc.nextLine().replaceAll("[\\\\[\\\\]]","").split(",");
    int[] nums = new int[parts.length];
    for (int i=0;i<parts.length;i++) nums[i]=Integer.parseInt(parts[i].trim());
    int target = sc.nextInt();
    Map<Integer,Integer> seen = new HashMap<>();
    for (int i=0;i<nums.length;i++) {
      if (seen.containsKey(target-nums[i])) {
        System.out.println("["+seen.get(target-nums[i])+", "+i+"]");
        return;
      }
      seen.put(nums[i], i);
    }
  }
}
''',
    cpp='''#include <iostream>
#include <sstream>
#include <vector>
#include <unordered_map>
using namespace std;
int main() {
  string line; getline(cin,line);
  vector<int> nums; string tok; stringstream ss(line.substr(1,line.size()-2));
  while(getline(ss,tok,',')) nums.push_back(stoi(tok));
  int target; cin>>target;
  unordered_map<int,int> seen;
  for (int i=0;i<(int)nums.size();i++) {
    if (seen.count(target-nums[i])) { cout<<"["<<seen[target-nums[i]]<<", "<<i<<"]"; return 0; }
    seen[nums[i]]=i;
  }
  return 0;
}
''',
    js='''const fs=require("fs");
const lines=fs.readFileSync(0,"utf8").trim().split("\\n");
const nums=JSON.parse(lines[0]);
const target=parseInt(lines[1],10);
const seen=new Map();
for (let i=0;i<nums.length;i++) {
  if (seen.has(target-nums[i])) { console.log(JSON.stringify([seen.get(target-nums[i]), i])); break; }
  seen.set(nums[i], i);
}
''',
)

PROBLEM_BANK = [
    {
        "slug": "echo-input", "title": "Echo Input", "difficulty": Difficulty.EASY, "topic": "basics",
        "tags": ["io", "strings"],
        "description": "Read one line from standard input and print it exactly as received.",
        "input_format": "A single line of text.", "output_format": "The same line.",
        "constraints": "Line length at most 1000 characters.",
        "starter_code": ECHO_STARTER,
        "test_cases": [
            {"name": "Sample 1", "input": "hello", "expected_output": "hello", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Sample 2", "input": "world", "expected_output": "world", "is_hidden": False, "is_sample": True, "sort_order": 1},
            {"name": "Hidden", "input": "secret-value", "expected_output": "secret-value", "is_hidden": True, "is_sample": False, "sort_order": 2},
        ],
    },
    {
        "slug": "add-two-numbers", "title": "Add Two Numbers", "difficulty": Difficulty.EASY, "topic": "basics",
        "tags": ["math", "io"],
        "description": "Given two integers, output their sum.",
        "input_format": "Two integers separated by a space.", "output_format": "One integer — the sum.",
        "constraints": "Each integer is between -10^6 and 10^6.",
        "starter_code": ADD_STARTER,
        "test_cases": [
            {"name": "Sample", "input": "2 3", "expected_output": "5", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "100 250", "expected_output": "350", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "reverse-string", "title": "Reverse String", "difficulty": Difficulty.EASY, "topic": "strings",
        "tags": ["strings"],
        "description": "Read a string and print its characters in reverse order.",
        "input_format": "One line containing a string.", "output_format": "The reversed string.",
        "constraints": "String length at most 1000.",
        "starter_code": REVERSE_STARTER,
        "test_cases": [
            {"name": "Sample", "input": "abc", "expected_output": "cba", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "racecar", "expected_output": "racecar", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "two-sum", "title": "Pair With Target Sum", "difficulty": Difficulty.EASY, "topic": "arrays",
        "tags": ["arrays", "hash-map"],
        "description": "Given an array of integers and a target, return indices of two distinct elements that sum to the target.\nAssume exactly one valid pair exists.",
        "input_format": "Line 1: array in JSON form e.g. [2,7,11,15]\nLine 2: target integer",
        "output_format": "Two indices as a JSON array e.g. [0,1]",
        "constraints": "Array length 2 to 10^4.",
        "starter_code": TWO_SUM_STARTER,
        "test_cases": [
            {"name": "Sample", "input": "[2,7,11,15]\n9", "expected_output": "[0, 1]", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "[3,2,4]\n6", "expected_output": "[1, 2]", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "max-element", "title": "Maximum Element", "difficulty": Difficulty.EASY, "topic": "arrays",
        "tags": ["arrays"],
        "description": "Given space-separated integers on one line, print the maximum value.",
        "input_format": "Space-separated integers.", "output_format": "Single integer — the maximum.",
        "constraints": "At most 10^5 numbers.",
        "starter_code": _starters(
            "nums = list(map(int, input().split()))\nprint(max(nums))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); int m=Integer.MIN_VALUE; while(sc.hasNextInt()) m=Math.max(m,sc.nextInt()); System.out.println(m);} }",
            "#include <iostream>\nusing namespace std;\nint main(){ int x,m=INT_MIN; while(cin>>x) m=max(m,x); cout<<m; return 0;}",
            "const fs=require('fs');\nconst nums=fs.readFileSync(0,'utf8').trim().split(/\\s+/).map(Number);\nconsole.log(Math.max(...nums));\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "3 1 9 2", "expected_output": "9", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "-5 -1 -9", "expected_output": "-1", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "count-vowels", "title": "Count Vowels", "difficulty": Difficulty.EASY, "topic": "strings",
        "tags": ["strings"],
        "description": "Count vowels (a,e,i,o,u, case-insensitive) in the given string.",
        "input_format": "One line string.", "output_format": "Integer count.",
        "constraints": "Length at most 10^5.",
        "starter_code": _starters(
            "s=input().strip().lower()\nprint(sum(1 for c in s if c in 'aeiou'))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ String s=new Scanner(System.in).nextLine().toLowerCase(); int c=0; for(char ch:s.toCharArray()) if(\"aeiou\".indexOf(ch)>=0) c++; System.out.println(c);} }",
            "#include <iostream>\n#include <string>\nusing namespace std;\nint main(){ string s; getline(cin,s); int c=0; for(char ch:s){ char l=tolower(ch); if(string(\"aeiou\").find(l)!=string::npos) c++; } cout<<c; return 0;}",
            "const fs=require('fs');\nconst s=fs.readFileSync(0,'utf8').trim().toLowerCase();\nconsole.log([...s].filter(c=>'aeiou'.includes(c)).length);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "Hello World", "expected_output": "3", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "xyz", "expected_output": "0", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "frequency-map", "title": "Character Frequency", "difficulty": Difficulty.EASY, "topic": "hash-maps",
        "tags": ["hash-map", "strings"],
        "description": "Given a string, print the character that appears most often. If tie, pick the lexicographically smallest character.",
        "input_format": "One lowercase string without spaces.", "output_format": "Single character.",
        "constraints": "Length 1 to 10^5.",
        "starter_code": _starters(
            "from collections import Counter\ns=input().strip()\nc=Counter(s)\nm=max(c.values())\nprint(min(ch for ch in c if c[ch]==m))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ String s=new Scanner(System.in).nextLine(); Map<Character,Integer> c=new HashMap<>(); for(char ch:s.toCharArray()) c.put(ch,c.getOrDefault(ch,0)+1); int m=0; char best='z'; for(var e:c.entrySet()){ if(e.getValue()>m||(e.getValue()==m&&e.getKey()<best)){ m=e.getValue(); best=e.getKey(); } } System.out.println(best);} }",
            "#include <iostream>\n#include <string>\n#include <map>\nusing namespace std;\nint main(){ string s; cin>>s; map<char,int> c; for(char ch:s) c[ch]++; int m=0; char best='z'; for(auto& p:c) if(p.second>m||(p.second==m&&p.first<best)){ m=p.second; best=p.first;} cout<<best; return 0;}",
            "const fs=require('fs');\nconst s=fs.readFileSync(0,'utf8').trim();\nconst c={}; for(const ch of s) c[ch]=(c[ch]||0)+1;\nlet m=0,b='z'; for(const ch of Object.keys(c).sort()){ if(c[ch]>m){m=c[ch];b=ch;} } console.log(b);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "aabbbcc", "expected_output": "b", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "aabb", "expected_output": "a", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "valid-parentheses", "title": "Balanced Brackets", "difficulty": Difficulty.EASY, "topic": "stack",
        "tags": ["stack", "strings"],
        "description": "Determine if a string containing only ()[]{} has properly nested brackets.",
        "input_format": "One bracket string.", "output_format": "true or false",
        "constraints": "Length at most 10^5.",
        "starter_code": _starters(
            "s=input().strip()\np={'(':')','[':']','{':'}'}\nst=[]\nfor ch in s:\n  if ch in p: st.append(p[ch])\n  elif not st or st.pop()!=ch: print('false'); exit()\nprint('true' if not st else 'false')\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ String s=new Scanner(System.in).nextLine(); Deque<Character> st=new ArrayDeque<>(); Map<Character,Character> p=Map.of('(',')','[',']','{','}'); for(char ch:s.toCharArray()){ if(p.containsKey(ch)) st.push(p.get(ch)); else if(st.isEmpty()||st.pop()!=ch){ System.out.println(\"false\"); return; } } System.out.println(st.isEmpty()?\"true\":\"false\");} }",
            "#include <iostream>\n#include <stack>\n#include <string>\nusing namespace std;\nint main(){ string s; cin>>s; stack<char> st; auto match=[](char o,char c){ return (o=='('&&c==')')||(o=='['&&c==']')||(o=='{'&&c=='}'); }; for(char ch:s){ if(ch=='('||ch=='['||ch=='{') st.push(ch); else { if(st.empty()||!match(st.top(),ch)){ cout<<\"false\"; return 0;} st.pop(); } } cout<<(st.empty()?\"true\":\"false\"); return 0;}",
            "const fs=require('fs');\nconst s=fs.readFileSync(0,'utf8').trim();\nconst p={')':'(','}':'{',']':'['};\nconst st=[];\nfor(const ch of s){ if('({['.includes(ch)) st.push(ch); else { const o=p[ch]; if(!st.length||st.pop()!==o){ console.log('false'); process.exit(0);} } }\nconsole.log(st.length?'false':'true');\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "([])", "expected_output": "true", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "([)]", "expected_output": "false", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "queue-simulation", "title": "Ticket Queue", "difficulty": Difficulty.EASY, "topic": "queue",
        "tags": ["queue", "simulation"],
        "description": "Simulate a ticket queue. Input: n people labeled 1..n. Each step removes front person and prints their label until queue empty.",
        "input_format": "Single integer n.", "output_format": "Space-separated labels in removal order.",
        "constraints": "1 <= n <= 10^5.",
        "starter_code": _starters(
            "n=int(input())\nq=list(range(1,n+1))\nprint(' '.join(map(str,q)))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ int n=new Scanner(System.in).nextInt(); StringBuilder sb=new StringBuilder(); for(int i=1;i<=n;i++){ if(i>1) sb.append(' '); sb.append(i);} System.out.println(sb);} }",
            "#include <iostream>\nusing namespace std;\nint main(){ int n; cin>>n; for(int i=1;i<=n;i++){ if(i>1) cout<<' '; cout<<i; } return 0;}",
            "const fs=require('fs');\nconst n=parseInt(fs.readFileSync(0,'utf8').trim(),10);\nconsole.log(Array.from({length:n},(_,i)=>i+1).join(' '));\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "5", "expected_output": "1 2 3 4 5", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "1", "expected_output": "1", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "linear-search", "title": "Linear Search Index", "difficulty": Difficulty.EASY, "topic": "searching",
        "tags": ["searching", "arrays"],
        "description": "Find the 0-based index of target in a space-separated list of integers. Print -1 if not found.",
        "input_format": "Line 1: space-separated integers\nLine 2: target integer",
        "output_format": "Single integer index or -1.",
        "constraints": "Array length at most 10^5.",
        "starter_code": _starters(
            "nums=list(map(int,input().split()))\nt=int(input())\nprint(next((i for i,x in enumerate(nums) if x==t), -1))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); String[] p=sc.nextLine().split(\" \"); int t=sc.nextInt(); for(int i=0;i<p.length;i++) if(Integer.parseInt(p[i])==t){ System.out.println(i); return;} System.out.println(-1);} }",
            "#include <iostream>\n#include <sstream>\n#include <vector>\nusing namespace std;\nint main(){ string line; getline(cin,line); int t; cin>>t; stringstream ss(line); int x,i=0; while(ss>>x){ if(x==t){ cout<<i; return 0;} i++; } cout<<-1; return 0;}",
            "const fs=require('fs');\nconst lines=fs.readFileSync(0,'utf8').trim().split('\\n');\nconst nums=lines[0].split(/\\s+/).map(Number);\nconst t=parseInt(lines[1],10);\nconsole.log(nums.indexOf(t));\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "4 2 7 2\n2", "expected_output": "1", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "1 2 3\n5", "expected_output": "-1", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "bubble-sort-count", "title": "Sort and Join", "difficulty": Difficulty.MEDIUM, "topic": "sorting",
        "tags": ["sorting", "arrays"],
        "description": "Sort the given integers in non-decreasing order and print them space-separated.",
        "input_format": "Space-separated integers.", "output_format": "Sorted integers space-separated.",
        "constraints": "At most 10^4 numbers.",
        "starter_code": _starters(
            "nums=sorted(map(int,input().split()))\nprint(' '.join(map(str,nums)))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); ArrayList<Integer> l=new ArrayList<>(); while(sc.hasNextInt()) l.add(sc.nextInt()); Collections.sort(l); for(int i=0;i<l.size();i++){ if(i>0) System.out.print(' '); System.out.print(l.get(i));} } }",
            "#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\nint main(){ vector<int> v; int x; while(cin>>x) v.push_back(x); sort(v.begin(),v.end()); for(size_t i=0;i<v.size();i++){ if(i) cout<<' '; cout<<v[i]; } return 0;}",
            "const fs=require('fs');\nconst nums=fs.readFileSync(0,'utf8').trim().split(/\\s+/).map(Number).sort((a,b)=>a-b);\nconsole.log(nums.join(' '));\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "3 1 2", "expected_output": "1 2 3", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "5 5 1", "expected_output": "1 5 5", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "factorial-recursive", "title": "Factorial", "difficulty": Difficulty.MEDIUM, "topic": "recursion",
        "tags": ["recursion", "math"],
        "description": "Compute n! for non-negative integer n.",
        "input_format": "Single integer n.", "output_format": "n factorial as integer.",
        "constraints": "0 <= n <= 12.",
        "starter_code": _starters(
            "def fact(n):\n  return 1 if n<=1 else n*fact(n-1)\nn=int(input())\nprint(fact(n))\n",
            "import java.util.*;\npublic class Main { static long fact(int n){ return n<=1?1:n*fact(n-1);} public static void main(String[] a){ System.out.println(fact(new Scanner(System.in).nextInt()));} }",
            "#include <iostream>\nusing namespace std;\nlong long fact(int n){ return n<=1?1:n*fact(n-1);} int main(){ int n; cin>>n; cout<<fact(n); return 0;}",
            "const fs=require('fs');\nconst fact=n=>n<=1?1:n*fact(n-1);\nconsole.log(fact(parseInt(fs.readFileSync(0,'utf8').trim(),10)));\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "5", "expected_output": "120", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "0", "expected_output": "1", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "list-node-sum", "title": "Linked List Sum", "difficulty": Difficulty.MEDIUM, "topic": "linked-lists",
        "tags": ["linked-list", "simulation"],
        "description": "A linked list is given as space-separated node values ending with -1 (null). Print the sum of all node values.",
        "input_format": "Space-separated integers ending with -1.", "output_format": "Single integer sum.",
        "constraints": "At most 10^5 nodes.",
        "starter_code": _starters(
            "vals=list(map(int,input().split()))\nprint(sum(v for v in vals if v!=-1))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); long s=0; while(sc.hasNextInt()){ int v=sc.nextInt(); if(v==-1) break; s+=v;} System.out.println(s);} }",
            "#include <iostream>\nusing namespace std;\nint main(){ long s=0,x; while(cin>>x){ if(x==-1) break; s+=x; } cout<<s; return 0;}",
            "const fs=require('fs');\nconst vals=fs.readFileSync(0,'utf8').trim().split(/\\s+/).map(Number);\nconsole.log(vals.filter(v=>v!==-1).reduce((a,b)=>a+b,0));\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "1 2 3 -1", "expected_output": "6", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "10 -1", "expected_output": "10", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "tree-height", "title": "Binary Tree Depth", "difficulty": Difficulty.MEDIUM, "topic": "trees",
        "tags": ["trees", "recursion"],
        "description": "A binary tree is given in level-order as space-separated values with -1 for missing nodes. Print the maximum depth.",
        "input_format": "Level-order values space-separated.", "output_format": "Integer depth.",
        "constraints": "At most 10^5 nodes.",
        "starter_code": _starters(
            "from collections import deque\nvals=list(map(int,input().split()))\nif not vals or vals[0]==-1: print(0); exit()\n# simplified: depth by levels until all remaining are -1\nd=0\ni=0\nn=len(vals)\nwhile i<n:\n  level=0\n  nxt=i\n  while i<n and level<(2**d if d else 1):\n    if vals[i]!=-1: nxt=max(nxt,i)\n    i+=1; level+=1\n  d+=1\nprint(d if vals[0]!=-1 else 0)\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ String[] p=new Scanner(System.in).nextLine().split(\" \"); int depth=0,i=0; while(i<p.length){ int sz=1<<depth, cnt=0; while(cnt<sz && i<p.length){ if(!p[i].equals(\"-1\")) depth=Math.max(depth, depth+1); i++; cnt++; } depth++; if(i>=p.length) break;} System.out.println(Math.max(1, depth-1));} }",
            "#include <iostream>\n#include <sstream>\n#include <vector>\nusing namespace std;\nint main(){ string line; getline(cin,line); stringstream ss(line); vector<string> v; string t; while(ss>>t) v.push_back(t); if(v.empty()||v[0]==\"-1\"){ cout<<0; return 0;} int depth=0,i=0; while(i<(int)v.size()){ int sz=1<<depth,cnt=0; while(cnt<sz&&i<(int)v.size()){ i++; cnt++; } depth++; } cout<<depth; return 0;}",
            "const fs=require('fs');\nconst vals=fs.readFileSync(0,'utf8').trim().split(/\\s+/);\nif(!vals.length||vals[0]==='-1'){console.log(0);process.exit(0);}\nlet depth=0,i=0;\nwhile(i<vals.length){const sz=1<<depth; let cnt=0; while(cnt<sz&&i<vals.length){i++; cnt++;} depth++;}\nconsole.log(depth);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "1 2 3 -1 -1", "expected_output": "2", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "-1", "expected_output": "0", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "two-pointers-pair", "title": "Sorted Pair Sum", "difficulty": Difficulty.MEDIUM, "topic": "two-pointers",
        "tags": ["two-pointers", "arrays"],
        "description": "In a sorted array, determine if any pair sums to target. Print yes or no.",
        "input_format": "Line 1: sorted integers\nLine 2: target",
        "output_format": "yes or no",
        "constraints": "Array length at most 10^5.",
        "starter_code": _starters(
            "nums=list(map(int,input().split()))\nt=int(input())\nl,r=0,len(nums)-1\nfound=False\nwhile l<r:\n  s=nums[l]+nums[r]\n  if s==t: found=True; break\n  elif s<t: l+=1\n  else: r-=1\nprint('yes' if found else 'no')\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); String[] p=sc.nextLine().split(\" \"); int t=sc.nextInt(); int l=0,r=p.length-1; boolean f=false; while(l<r){ int s=Integer.parseInt(p[l])+Integer.parseInt(p[r]); if(s==t){f=true;break;} else if(s<t) l++; else r--; } System.out.println(f?\"yes\":\"no\");} }",
            "#include <iostream>\n#include <sstream>\n#include <vector>\nusing namespace std;\nint main(){ string line; getline(cin,line); int t; cin>>t; stringstream ss(line); vector<int> v; int x; while(ss>>x) v.push_back(x); int l=0,r=v.size()-1; bool f=false; while(l<r){ int s=v[l]+v[r]; if(s==t){f=true;break;} else if(s<t) l++; else r--; } cout<<(f?\"yes\":\"no\"); return 0;}",
            "const fs=require('fs');\nconst lines=fs.readFileSync(0,'utf8').trim().split('\\n');\nconst nums=lines[0].split(/\\s+/).map(Number);\nconst t=parseInt(lines[1],10);\nlet l=0,r=nums.length-1,f=false;\nwhile(l<r){const s=nums[l]+nums[r]; if(s===t){f=true;break;} else if(s<t) l++; else r--;}\nconsole.log(f?'yes':'no');\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "1 2 4 6\n8", "expected_output": "yes", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "1 2 3\n10", "expected_output": "no", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "sliding-window-max", "title": "Window Maximum Sum", "difficulty": Difficulty.MEDIUM, "topic": "sliding-window",
        "tags": ["sliding-window", "arrays"],
        "description": "Given array and window size k, print the maximum sum among all contiguous windows of size k.",
        "input_format": "Line 1: space-separated integers\nLine 2: k",
        "output_format": "Maximum window sum.",
        "constraints": "1 <= k <= n <= 10^5.",
        "starter_code": _starters(
            "nums=list(map(int,input().split()))\nk=int(input())\ncur=sum(nums[:k])\nbest=cur\nfor i in range(k,len(nums)):\n  cur+=nums[i]-nums[i-k]\n  best=max(best,cur)\nprint(best)\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); String[] p=sc.nextLine().split(\" \"); int k=sc.nextInt(); int[] nums=new int[p.length]; for(int i=0;i<p.length;i++) nums[i]=Integer.parseInt(p[i]); long cur=0,best=Long.MIN_VALUE; for(int i=0;i<nums.length;i++){ cur+=nums[i]; if(i>=k) cur-=nums[i-k]; if(i>=k-1) best=Math.max(best,cur);} System.out.println(best);} }",
            "#include <iostream>\n#include <sstream>\n#include <vector>\n#include <climits>\nusing namespace std;\nint main(){ string line; getline(cin,line); int k; cin>>k; stringstream ss(line); vector<int> v; int x; while(ss>>x) v.push_back(x); long cur=0,best=LLONG_MIN; for(int i=0;i<(int)v.size();i++){ cur+=v[i]; if(i>=k) cur-=v[i-k]; if(i>=k-1) best=max(best,cur);} cout<<best; return 0;}",
            "const fs=require('fs');\nconst lines=fs.readFileSync(0,'utf8').trim().split('\\n');\nconst nums=lines[0].split(/\\s+/).map(Number);\nconst k=parseInt(lines[1],10);\nlet cur=0,best=-Infinity;\nfor(let i=0;i<nums.length;i++){ cur+=nums[i]; if(i>=k) cur-=nums[i-k]; if(i>=k-1) best=Math.max(best,cur);}\nconsole.log(best);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "1 4 2 10 2\n3", "expected_output": "16", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "5 5 5\n2", "expected_output": "10", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "binary-search", "title": "Binary Search", "difficulty": Difficulty.MEDIUM, "topic": "binary-search",
        "tags": ["binary-search", "arrays"],
        "description": "Find 0-based index of target in sorted array using binary search. Print -1 if absent.",
        "input_format": "Line 1: sorted integers\nLine 2: target",
        "output_format": "Index or -1.",
        "constraints": "Array length at most 10^5.",
        "starter_code": _starters(
            "nums=list(map(int,input().split()))\nt=int(input())\nl,r=0,len(nums)-1\nans=-1\nwhile l<=r:\n  m=(l+r)//2\n  if nums[m]==t: ans=m; break\n  elif nums[m]<t: l=m+1\n  else: r=m-1\nprint(ans)\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); String[] p=sc.nextLine().split(\" \"); int t=sc.nextInt(); int l=0,r=p.length-1,ans=-1; while(l<=r){ int m=(l+r)/2; int v=Integer.parseInt(p[m]); if(v==t){ans=m;break;} else if(v<t) l=m+1; else r=m-1;} System.out.println(ans);} }",
            "#include <iostream>\n#include <sstream>\n#include <vector>\nusing namespace std;\nint main(){ string line; getline(cin,line); int t; cin>>t; stringstream ss(line); vector<int> v; int x; while(ss>>x) v.push_back(x); int l=0,r=v.size()-1,ans=-1; while(l<=r){ int m=(l+r)/2; if(v[m]==t){ans=m;break;} else if(v[m]<t) l=m+1; else r=m-1;} cout<<ans; return 0;}",
            "const fs=require('fs');\nconst lines=fs.readFileSync(0,'utf8').trim().split('\\n');\nconst nums=lines[0].split(/\\s+/).map(Number);\nconst t=parseInt(lines[1],10);\nlet l=0,r=nums.length-1,ans=-1;\nwhile(l<=r){const m=(l+r>>1); if(nums[m]===t){ans=m;break;} else if(nums[m]<t) l=m+1; else r=m-1;}\nconsole.log(ans);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "1 3 5 7\n5", "expected_output": "2", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "2 4 6\n3", "expected_output": "-1", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "climb-stairs", "title": "Ways to Climb", "difficulty": Difficulty.MEDIUM, "topic": "dynamic-programming",
        "tags": ["dynamic-programming"],
        "description": "You can climb 1 or 2 steps at a time. Given n steps, print the number of distinct ways to reach the top.",
        "input_format": "Integer n.", "output_format": "Number of ways.",
        "constraints": "1 <= n <= 45.",
        "starter_code": _starters(
            "n=int(input())\na,b=1,1\nfor _ in range(n-1): a,b=b,a+b\nprint(b)\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ int n=new Scanner(System.in).nextInt(); long x=1,y=1; for(int i=1;i<n;i++){ long t=x+y; x=y; y=t;} System.out.println(y);} }",
            "#include <iostream>\nusing namespace std;\nint main(){ int n; cin>>n; long long a=1,b=1; for(int i=1;i<n;i++){ long long t=a+b; a=b; b=t;} cout<<b; return 0;}",
            "const fs=require('fs');\nlet n=parseInt(fs.readFileSync(0,'utf8').trim(),10);\nlet a=1,b=1;\nfor(let i=1;i<n;i++){ const t=a+b; a=b; b=t;}\nconsole.log(b);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "3", "expected_output": "3", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "1", "expected_output": "1", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "longest-increasing", "title": "Longest Increasing Subsequence Length", "difficulty": Difficulty.HARD, "topic": "dynamic-programming",
        "tags": ["dynamic-programming", "arrays"],
        "description": "Print the length of the longest strictly increasing subsequence.",
        "input_format": "Space-separated integers.", "output_format": "Single integer length.",
        "constraints": "At most 5000 numbers.",
        "starter_code": _starters(
            "nums=list(map(int,input().split()))\ndp=[]\nfor x in nums:\n  import bisect\n  i=bisect.bisect_left(dp,x)\n  if i==len(dp): dp.append(x)\n  else: dp[i]=x\nprint(len(dp))\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); ArrayList<Integer> dp=new ArrayList<>(); while(sc.hasNextInt()){ int x=sc.nextInt(); int i=Collections.binarySearch(dp,x); if(i<0) i=-i-1; if(i==dp.size()) dp.add(x); else dp.set(i,x);} System.out.println(dp.size());} }",
            "#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\nint main(){ vector<int> dp; int x; while(cin>>x){ auto it=lower_bound(dp.begin(),dp.end(),x); if(it==dp.end()) dp.push_back(x); else *it=x; } cout<<dp.size(); return 0;}",
            "const fs=require('fs');\nconst nums=fs.readFileSync(0,'utf8').trim().split(/\\s+/).map(Number);\nconst dp=[];\nfor(const x of nums){ let l=0,r=dp.length; while(l<r){const m=(l+r>>1); if(dp[m]<x) l=m+1; else r=m;} if(l===dp.length) dp.push(x); else dp[l]=x;}\nconsole.log(dp.length);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "10 9 2 5 3 7 101 18", "expected_output": "4", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "1 2 3 4", "expected_output": "4", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "merge-intervals-count", "title": "Non-Overlapping Intervals", "difficulty": Difficulty.HARD, "topic": "arrays",
        "tags": ["greedy", "sorting"],
        "description": "Given n intervals as pairs start end on separate lines, print the minimum number of intervals to remove so the rest do not overlap.",
        "input_format": "Line 1: n\nNext n lines: start end",
        "output_format": "Minimum removals.",
        "constraints": "n <= 10^5.",
        "starter_code": _starters(
            "n=int(input())\niv=[]\nfor _ in range(n):\n  a,b=map(int,input().split())\n  iv.append((a,b))\niv.sort(key=lambda x:x[1])\nend=-10**18\nkeep=0\nfor a,b in iv:\n  if a>=end: keep+=1; end=b\nprint(n-keep)\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); int n=sc.nextInt(); int[][] iv=new int[n][2]; for(int i=0;i<n;i++){ iv[i][0]=sc.nextInt(); iv[i][1]=sc.nextInt(); } Arrays.sort(iv,(x,y)->Integer.compare(x[1],y[1])); long end=Long.MIN_VALUE; int keep=0; for(int[] p:iv){ if(p[0]>=end){ keep++; end=p[1]; } } System.out.println(n-keep);} }",
            "#include <iostream>\n#include <vector>\n#include <algorithm>\nusing namespace std;\nint main(){ int n; cin>>n; vector<pair<long long,long long>> iv(n); for(int i=0;i<n;i++) cin>>iv[i].first>>iv[i].second; sort(iv.begin(),iv.end(),[](auto&a,auto&b){return a.second<b.second;}); long long end=LLONG_MIN/2; int keep=0; for(auto& p:iv){ if(p.first>=end){ keep++; end=p.second; } } cout<<n-keep; return 0;}",
            "const fs=require('fs');\nconst lines=fs.readFileSync(0,'utf8').trim().split('\\n');\nconst n=parseInt(lines[0],10);\nconst iv=lines.slice(1,n+1).map(l=>l.split(/\\s+/).map(Number));\niv.sort((a,b)=>a[1]-b[1]);\nlet end=-1e18, keep=0;\nfor(const [a,b] of iv){ if(a>=end){ keep++; end=b; } }\nconsole.log(n-keep);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "3\n1 2\n2 3\n3 4", "expected_output": "0", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "2\n1 3\n2 4", "expected_output": "1", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
    {
        "slug": "matrix-path-sum", "title": "Grid Minimum Path Sum", "difficulty": Difficulty.HARD, "topic": "dynamic-programming",
        "tags": ["dynamic-programming", "matrix"],
        "description": "Given an r x c grid of non-negative integers (rows space-separated), find minimum sum path from top-left to bottom-right moving only right or down.",
        "input_format": "Line 1: r c\nNext r lines: c integers",
        "output_format": "Minimum path sum.",
        "constraints": "Grid at most 200 x 200.",
        "starter_code": _starters(
            "r,c=map(int,input().split())\ngrid=[list(map(int,input().split())) for _ in range(r)]\nfor i in range(r):\n  for j in range(c):\n    if i==0 and j==0: continue\n    top=grid[i-1][j] if i else 10**9\n    left=grid[i][j-1] if j else 10**9\n    grid[i][j]+=min(top,left)\nprint(grid[-1][-1])\n",
            "import java.util.*;\npublic class Main { public static void main(String[] a){ Scanner sc=new Scanner(System.in); int r=sc.nextInt(), c=sc.nextInt(); int[][] g=new int[r][c]; for(int i=0;i<r;i++) for(int j=0;j<c;j++) g[i][j]=sc.nextInt(); for(int i=0;i<r;i++) for(int j=0;j<c;j++){ if(i==0&&j==0) continue; int top=i>0?g[i-1][j]:Integer.MAX_VALUE; int left=j>0?g[i][j-1]:Integer.MAX_VALUE; g[i][j]+=Math.min(top,left);} System.out.println(g[r-1][c-1]);} }",
            "#include <iostream>\n#include <vector>\n#include <climits>\nusing namespace std;\nint main(){ int r,c; cin>>r>>c; vector<vector<int>> g(r,vector<int>(c)); for(int i=0;i<r;i++) for(int j=0;j<c;j++) cin>>g[i][j]; for(int i=0;i<r;i++) for(int j=0;j<c;j++){ if(i==0&&j==0) continue; int top=i?g[i-1][j]:INT_MAX; int left=j?g[i][j-1]:INT_MAX; g[i][j]+=min(top,left);} cout<<g[r-1][c-1]; return 0;}",
            "const fs=require('fs');\nconst lines=fs.readFileSync(0,'utf8').trim().split('\\n');\nconst [r,c]=lines[0].split(/\\s+/).map(Number);\nconst g=lines.slice(1,1+r).map(l=>l.split(/\\s+/).map(Number));\nfor(let i=0;i<r;i++) for(let j=0;j<c;j++){ if(i===0&&j===0) continue; const top=i?g[i-1][j]:1e9; const left=j?g[i][j-1]:1e9; g[i][j]+=Math.min(top,left);}\nconsole.log(g[r-1][c-1]);\n",
        ),
        "test_cases": [
            {"name": "Sample", "input": "2 2\n1 3\n2 1", "expected_output": "4", "is_hidden": False, "is_sample": True, "sort_order": 0},
            {"name": "Hidden", "input": "1 3\n1 2 3", "expected_output": "6", "is_hidden": True, "is_sample": False, "sort_order": 1},
        ],
    },
]
