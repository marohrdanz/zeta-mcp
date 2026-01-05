import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function App() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/api/mcp/tasks`)
      .then(res => res.json())
      .then(data => {setTasks(data.tasks.map(task => ({
          id: task.id,
          title: task.title,
          description: task.description,
          status: task.status
      })))})
  }, []);

  return (
    <div className="App">
      <Header />
      <TaskList tasks={tasks} />
    </div>
  );
}

function Header() {
  return (
    <header className="App-header">
      <h1>Welcome to the MCP Task Manager</h1>
    </header>
  );
}

function TaskList({ tasks }) {
  return (
    <div>
      <h2>Tasks</h2>
      <ol>
        {tasks.map(task => <li key={task.id}>{task.title}: {task.status}</li>)}
      </ol>
    </div>
  );
}


export default App
