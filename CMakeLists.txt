cmake_minimum_required(VERSION 3.10)
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
  # EXTREME LINT CONTROL
  # We do NOT use ament_lint_auto because it's too aggressive with experimental folders.
  
  # Only run flake8/pep257/copyright on the core Python package directory.
  # This avoids scanning skills/ or scripts/experimental/
  
  find_package(ament_cmake_copyright REQUIRED)
  ament_copyright(DIRECTORY ${PROJECT_NAME})

  find_package(ament_cmake_flake8 REQUIRED)
  ament_flake8(DIRECTORY ${PROJECT_NAME})

  find_package(ament_cmake_pep257 REQUIRED)
  ament_pep257(DIRECTORY ${PROJECT_NAME})

  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_skills_guidelines test/test_skills_guidelines.py
    TIMEOUT 30
  )
endif()

ament_package()
