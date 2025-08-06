# 🎯 Interactive DFD Workshop Guide

## 🚀 **Perfect Setup for Client Workshops**

Your Threat Modeling Pipeline now has **professional interactive capabilities** designed specifically for client workshops where you drive the threat modeling process.

---

## 📋 **Pre-Workshop Setup**

### 1. **Start the System**
```bash
# Terminal 1 - Backend
cd apps/api
source venv/bin/activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend  
cd apps/web
npm run dev
```

### 2. **Navigate to**: http://localhost:3001

### 3. **Load Sample Data** (Optional)
- Run: `python test_interactive_mermaid.py` to set up enhanced demo data

---

## 🎨 **Workshop Flow & Features**

### **Phase 1: Document Upload & Analysis**
1. **Upload Client Documents**
   - Drag & drop architecture documents
   - Show real-time file validation
   - Demonstrate text extraction

2. **AI-Powered DFD Extraction**
   - Click "Start DFD Extraction"
   - Show extraction progress
   - Display component summary

### **Phase 2: Interactive DFD Review** ⭐
Navigate to **DFD Review** step - this is where the magic happens!

#### **Available Views:**
- **📝 Edit JSON**: Direct JSON editing
- **👁 Interactive Diagram**: Full-featured visual diagram
- **📊 Workshop View**: Split-screen for live editing demo
- **📋 Mermaid Code**: Export-ready code

---

## 🎯 **Workshop View Features (Recommended)**

### **Split-Screen Experience**
- **Left Side**: Live JSON editor
- **Right Side**: Real-time diagram rendering
- **Perfect for**: Demonstrating iterative threat modeling

### **Interactive Controls**
- **🔍 Zoom In/Out**: Mouse wheel or buttons
- **🖱 Pan**: Click and drag around large diagrams  
- **📺 Fullscreen**: Perfect for presentation mode
- **💾 Export PNG**: Generate client deliverables
- **🔄 Reset View**: Return to center/default zoom

---

## 👥 **Client Interaction Strategies**

### **1. Start with "Interactive Diagram" View**
- Show the complete visual overview
- Use fullscreen for maximum impact
- Navigate around the diagram together

### **2. Switch to "Workshop View" for Collaboration**
- Edit JSON on the left while discussing
- Watch diagram update in real-time on the right
- Perfect for "What if we add..." scenarios

### **3. Demonstrate Threat Modeling Process**
```json
// Example: Adding a new threat vector
{
  "external_entities": [
    "Customer",
    "Admin", 
    "Malicious Actor"  // ← Add this live
  ]
}
```

### **4. Export Results**
- Use PNG export for immediate deliverables
- Copy Mermaid code for documentation
- Save JSON for further analysis

---

## 🎪 **Workshop Demonstration Scripts**

### **Script 1: Component Addition**
*"Let's add a new external threat actor and see how it affects our model..."*
1. Switch to Workshop View
2. Add `"Malicious Insider"` to external_entities
3. Show real-time diagram update
4. Discuss implications

### **Script 2: Data Flow Analysis**
*"Now let's trace this sensitive data flow..."*
1. Use Interactive Diagram view
2. Zoom into specific component
3. Follow data flow connections
4. Identify potential vulnerabilities

### **Script 3: Trust Boundary Review**
*"Let's examine our security perimeters..."*
1. Point out trust boundary representations
2. Discuss security controls at each boundary
3. Use fullscreen for better visibility

---

## 💡 **Pro Tips for Workshops**

### **Visual Impact**
- Start in fullscreen Interactive Diagram mode
- Use high zoom levels for complex sections
- Export diagrams immediately for meeting notes

### **Client Engagement**
- Let clients suggest components to add/remove
- Use Workshop View for collaborative editing
- Show real-time validation and error handling

### **Technical Demonstration**
- Switch between all tabs to show capabilities
- Demonstrate export functionality
- Show JSON → Visual transformation

### **Follow-up Materials**
- Export final PNG diagrams
- Provide Mermaid code for their documentation
- Share JSON files for future analysis

---

## 🚨 **Troubleshooting**

### **If Diagram Doesn't Render**
- Check console for JSON syntax errors
- Verify component name matching in data flows
- Use the JSON editor tab to fix syntax

### **Performance with Large Diagrams**
- Use zoom controls to focus on sections
- Reset view if navigation gets confusing
- Export sections separately if needed

### **Browser Compatibility**
- Tested on Chrome, Firefox, Safari
- Use fullscreen mode for older displays
- Ensure JavaScript is enabled

---

## 🎯 **Success Metrics**

A successful workshop includes:
- ✅ Client actively participating in DFD editing
- ✅ Real-time visualization of changes
- ✅ Exported diagrams for deliverables
- ✅ Clear understanding of threat modeling process
- ✅ Interactive discussion of security implications

---

**🚀 Your system is now ready for professional client workshops with full interactive capabilities!**