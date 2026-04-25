cmake_minimum_required(VERSION 3.8)
project(bob_central)

find_package(ament_cmake REQUIRED)

ament_python_install_package(${PROJECT_NAME}
  SETUP_CFG
    ${PROJECT_NAME}/setup.cfg
  SCRIPTS_DESTINATION
    lib/${PROJECT_NAME}
)

# Install data files
install(
  DIRECTORY launch prompts config skills
  DESTINATION share/${PROJECT_NAME}
)

# Install meta-data
install(
  FILES package.xml
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  # Manual linting setup to avoid Eva's experimental chaos
  # We only lint the core package directory and the setup script
  
  find_package(ament_cmake_copyright REQUIRED)
  ament_copyright(EXCLUDE skills setup.py)

  find_package(ament_cmake_flake8 REQUIRED)
  ament_flake8(EXCLUDE 
    skills/repl_kernel/scripts/health_check.py
    skills/social_memory/scripts/search_history.py
    skills/swarm_connector/scripts/swarm_connector.py
    setup.py
  )

  find_package(ament_cmake_pep257 REQUIRED)
  ament_pep257(EXCLUDE 
    skills/repl_kernel/scripts/health_check.py
    skills/social_memory/scripts/search_history.py
    skills/swarm_connector/scripts/swarm_connector.py
    setup.py
  )

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_skills_guidelines test/test_skills_guidelines.py
    TIMEOUT 30
  )
endif()

ament_package()
